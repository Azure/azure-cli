# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest.mock import Mock, patch
from azure.cli.command_modules.aro._dynamic_validators import (
    can_do_action,
    dyn_validate_cidr_ranges,
    dyn_validate_subnet_and_route_tables,
    dyn_validate_vnet,
    dyn_validate_resource_permissions,
    dyn_validate_version,
    dyn_validate_managed_identity_delete_permissions
)

from azure.mgmt.authorization.models import Permission
import pytest

test_can_do_action_data = [
    (
        "empty permissions list",
        [],
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        False
    ),
    (
        "has permission - exact",
        [
            Permission(actions=["Microsoft.Compute/virtualMachines/*"], not_actions=[]),
            Permission(actions=["Microsoft.Network/virtualNetworks/subnets/join/action"], not_actions=[]),
        ],
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        True
    ),
    (
        "has permission - wildcard",
        [
            Permission(actions=["Microsoft.Network/virtualNetworks/subnets/*/action"], not_actions=[]),
        ],
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        True
    ),
    (
        "has permission - exact, conflict",
        [
            Permission(actions=[], not_actions=["Microsoft.Network/virtualNetworks/subnets/join/action"]),
            Permission(actions=["Microsoft.Network/virtualNetworks/subnets/join/action"], not_actions=[]),
        ],
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        True
    ),
    (
        "has permission excluded - exact",
        [
            Permission(actions=["Microsoft.Network/*"], not_actions=["Microsoft.Network/virtualNetworks/subnets/join/action"]),
        ],
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        False
    ),
    (
        "has permission excluded - wildcard",
        [
            Permission(actions=["Microsoft.Network/*"], not_actions=["Microsoft.Network/virtualNetworks/subnets/*/action"]),
        ],
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        False
    )
]


@pytest.mark.parametrize(
    "test_description, perms, action, expected",
    test_can_do_action_data,
    ids=[i[0] for i in test_can_do_action_data]
)
def test_can_do_action(
    test_description, perms, action, expected
):
    actual = can_do_action(perms, action)

    if actual != expected:
        raise Exception(f"Error mismatch, expected: {expected}, actual: {actual}")


test_validate_cidr_data = [
    (
        "should return no error on address_prefix set on subnets, no additional cidrs, no overlap",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        [{"addressPrefix": "172.143.5.0/24"}, {"addressPrefix": "172.143.4.0/25"}],
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        None
    ),
    (
        "should return no error on address_prefix set on subnets, additional cidrs, no overlap",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr="172.142.0.0/21", service_cidr="172.143.6.0/25"),
        [{"addressPrefix": "172.143.4.0/24"}, {"addressPrefix": "172.143.5.0/25"}],
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        None
    ),
    (
        "should return no error on multiple address_prefixes set on subnets, additional cidrs, no overlap",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr="172.142.0.0/21", service_cidr="172.143.6.0/25"),
        [{"addressPrefixes": ["172.143.4.0/24", "172.143.8.0/25"]}, {"addressPrefixes": ["172.143.5.0/25", "172.143.9.0/24"]}],
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        None
    ),
    (
        "should error on address_prefix set on subnets, no additional cidrs, overlap",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        [{"addressPrefix": "172.143.4.0/24"}, {"addressPrefix": "172.143.4.0/25"}],
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        "172.143.4.0/24 is not valid as it overlaps with 172.143.4.0/25"
    ),
    (
        "should return error on pod cidr not having enough addresses to create cluster",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr="172.143.4.0/24", service_cidr=None),
        [{'addressPrefix': "172.143.5.0/24"}, {'addressPrefix': "172.143.4.0/25"}],
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        "172.143.4.0/24 does not contain enough addresses for 3 master nodes (Requires cidr prefix of 21 or lower)"
    ),
]


@pytest.mark.parametrize(
    "test_description, cmd_mock, namespace_mock, get_subnet_mock_side_effect, parse_resource_id_mock_return_value, expected_addresses",
    test_validate_cidr_data,
    ids=[i[0] for i in test_validate_cidr_data]
)
@patch('azure.cli.command_modules.aro._dynamic_validators.get_subnet')
@patch('azure.cli.command_modules.aro._dynamic_validators.parse_resource_id')
def test_validate_cidr(
    # Mocked functions:
    parse_resource_id_mock, get_subnet_mock,

    # Test cases parameters:
    test_description, cmd_mock, namespace_mock, get_subnet_mock_side_effect, parse_resource_id_mock_return_value, expected_addresses
):
    parse_resource_id_mock.return_value = parse_resource_id_mock_return_value
    get_subnet_mock.side_effect = get_subnet_mock_side_effect

    validate_cidr_fn = dyn_validate_cidr_ranges()
    if expected_addresses is None:
        addresses = validate_cidr_fn(cmd_mock, namespace_mock)

        if (len(addresses) > 0):
            raise Exception(f"Unexpected Error: {addresses[0]}")
    else:
        addresses = validate_cidr_fn(cmd_mock, namespace_mock)

        if (addresses[0][3] != expected_addresses):
            raise Exception(f"Error returned was not expected\n Expected : {expected_addresses}\n Actual   : {addresses[0][3]}")


test_validate_subnets_data = [
    (
        "should not return missing permission when actions are permitted",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        {'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=["Microsoft.Network/routeTables/*"], not_actions=[])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        None
    ),
    (
        "should return missing permission when actions are not permitted",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        {'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=[], not_actions=["Microsoft.Network/routeTables/*"])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        "Microsoft.Network/routeTables/join/action permission is missing"
    ),
    (
        "should return missing permission when actions are not present",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        {'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=[], not_actions=[])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        "Microsoft.Network/routeTables/join/action permission is missing"
    ),
    (
        "should return message when network security group is already attached to subnet",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None, enable_preconfigured_nsg=None),
        {'networkSecurityGroup': {'id': 'test'}, 'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=["Microsoft.Network/routeTables/*"], not_actions=[])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        "A Network Security Group \"test\" is already assigned to this subnet. "
        "Ensure there are no Network Security Groups assigned to cluster "
        "subnets before cluster creation"
    ),
    (
        "should not return message when Preconfigured NSG is enabled and network security group is attached to subnet",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None, enable_preconfigured_nsg=True),
        {'networkSecurityGroup': {'id': 'test'}, 'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=["Microsoft.Network/routeTables/*"], not_actions=[])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        None
    )
]


@pytest.mark.parametrize(
    "test_description, cmd_mock, namespace_mock, get_subnet_mock_return_value, auth_client_mock, parse_resource_id_mock_return_value, is_valid_resource_id_mock_return_value, expected_missing_perms",
    test_validate_subnets_data,
    ids=[i[0] for i in test_validate_subnets_data]
)
@patch('azure.cli.command_modules.aro._dynamic_validators.get_subnet')
@patch('azure.cli.command_modules.aro._dynamic_validators.get_mgmt_service_client')
@patch('azure.cli.command_modules.aro._dynamic_validators.parse_resource_id')
@patch('azure.cli.command_modules.aro._dynamic_validators.is_valid_resource_id')
def test_validate_subnets(
    # Mocked functions:
    is_valid_resource_id_mock, parse_resource_id_mock, get_mgmt_service_client_mock, get_subnet_mock,

    # Test cases parameters:
    test_description, cmd_mock, namespace_mock, get_subnet_mock_return_value, auth_client_mock, parse_resource_id_mock_return_value, is_valid_resource_id_mock_return_value, expected_missing_perms
):
    is_valid_resource_id_mock.return_value = is_valid_resource_id_mock_return_value
    parse_resource_id_mock.return_value = parse_resource_id_mock_return_value
    get_mgmt_service_client_mock.side_effect = [auth_client_mock]
    get_subnet_mock.return_value = get_subnet_mock_return_value

    validate_subnet_fn = dyn_validate_subnet_and_route_tables('')
    if expected_missing_perms is None:
        missing_perms = validate_subnet_fn(cmd_mock, namespace_mock)

        if (len(missing_perms) > 0):
            raise Exception(f"Unexpected Permission Missing: {missing_perms[0]}")
    else:
        missing_perms = validate_subnet_fn(cmd_mock, namespace_mock)

        if (missing_perms[0][3] != expected_missing_perms):
            raise Exception(f"Error returned was not expected\n Expected : {expected_missing_perms}\n Actual   : {missing_perms[0][3]}")


test_validate_vnets_data = [
    (
        "should not return missing permission when actions are permitted",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        {'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=["Microsoft.Network/virtualNetworks/*"], not_actions=[])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        None
    ),
    (
        "should return disabled permission when actions are not permitted",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        {'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=[], not_actions=["Microsoft.Network/virtualNetworks/*"])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        "Microsoft.Network/virtualNetworks/join/action permission is missing"
    ),
    (
        "should return missing permission when actions are not present",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(vnet='', key="192.168.0.1/32", master_subnet='', worker_subnet='', pod_cidr=None, service_cidr=None),
        {'routeTable': {'id': 'test'}},
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=[], not_actions=[])]}),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        Mock(),
        "Microsoft.Network/virtualNetworks/join/action permission is missing"
    )
]


@pytest.mark.parametrize(
    "test_description, cmd_mock, namespace_mock, get_vnet_mock_return_value, auth_client_mock, parse_resource_id_mock_return_value, is_valid_resource_id_mock_return_value, expected_missing_perms",
    test_validate_vnets_data,
    ids=[i[0] for i in test_validate_vnets_data]
)
@patch('azure.cli.command_modules.aro._dynamic_validators.get_vnet')
@patch('azure.cli.command_modules.aro._dynamic_validators.get_mgmt_service_client')
@patch('azure.cli.command_modules.aro._dynamic_validators.parse_resource_id')
@patch('azure.cli.command_modules.aro._dynamic_validators.is_valid_resource_id')
def test_validate_vnets(
    # Mocked functions:
    is_valid_resource_id_mock, parse_resource_id_mock, get_mgmt_service_client_mock, get_vnet_mock,

    # Test cases parameters:
    test_description, cmd_mock, namespace_mock, get_vnet_mock_return_value, auth_client_mock, parse_resource_id_mock_return_value, is_valid_resource_id_mock_return_value, expected_missing_perms
):
    is_valid_resource_id_mock.return_value = is_valid_resource_id_mock_return_value
    parse_resource_id_mock.return_value = parse_resource_id_mock_return_value
    get_mgmt_service_client_mock.side_effect = [auth_client_mock]
    get_vnet_mock.return_value = get_vnet_mock_return_value

    validate_vnet_fn = dyn_validate_vnet("vnet")
    if expected_missing_perms is None:
        missing_perms = validate_vnet_fn(cmd_mock, namespace_mock)

        if (len(missing_perms) > 0):
            raise Exception(f"Unexpected Permission Missing: {missing_perms[0]}")
    else:
        missing_perms = validate_vnet_fn(cmd_mock, namespace_mock)

        if (missing_perms[0][3] != expected_missing_perms):
            raise Exception(f"Error returned was not expected\n Expected : {expected_missing_perms}\n Actual   : {missing_perms[0][3]}")


test_validate_resource_data = [
    (
        "should not return missing permission when role assignments are assigned",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": None,
            "child_name_1": None
        },
        [True, True, True, True, True, True, True, True],
        None
    ),
    (
        "should return missing permission when role assignments are not assigned",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(),
        {
            "subscription": "subscription",
            "namespace": "MICROSOFT.NETWORK",
            "type": "virtualnetworks",
            "last_child_num": 1,
            "child_type_1": "subnets",
            "resource_group": None,
            "name": "Test_Subnet",
            "child_name_1": None
        },
        [True, True, True, True, True, True, True, False],
        "Resource Test_Subnet is missing role assignment test for service principal test " +
        "(These roles will be automatically added during cluster creation)"
    )
]


@pytest.mark.parametrize(
    "test_description, cmd_mock, namespace_mock, parse_resource_id_mock_return_value, has_role_assignment_on_resource_mock_return_value, expected_missing_perms",
    test_validate_resource_data,
    ids=[i[0] for i in test_validate_resource_data]
)
@patch('azure.cli.command_modules.aro._dynamic_validators.has_role_assignment_on_resource')
@patch('azure.cli.command_modules.aro._dynamic_validators.parse_resource_id')
def test_validate_resources(
    # Mocked functions:
    parse_resource_id_mock, has_role_assignment_on_resource_mock,

    # Test cases parameters:
    test_description, cmd_mock, namespace_mock, parse_resource_id_mock_return_value, has_role_assignment_on_resource_mock_return_value, expected_missing_perms
):
    parse_resource_id_mock.return_value = parse_resource_id_mock_return_value
    has_role_assignment_on_resource_mock.side_effect = has_role_assignment_on_resource_mock_return_value

    sp_ids = ["test", "test"]
    resources = {"test": "test", "test": "test"}
    validate_res_perms_fn = dyn_validate_resource_permissions(sp_ids, resources)
    if expected_missing_perms is None:
        missing_perms = validate_res_perms_fn(cmd_mock, namespace_mock)

        if (len(missing_perms) > 0):
            raise Exception(f"Unexpected Permission Missing: {missing_perms[0]}")
    else:
        missing_perms = validate_res_perms_fn(cmd_mock, namespace_mock)

        if (missing_perms[0][3] != expected_missing_perms):
            raise Exception(f"Error returned was not expected\n Expected : {expected_missing_perms}\n Actual   : {missing_perms[0][3]}")


test_validate_version_data = [
    (
        "should not return error when visibility is Public",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(version="4.9.10"),
        ["4.9.10"],
        None
    ),
    (
        "should return error when visibility is random string",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(version="72.2343.21212"),
        ["4.9.10"],
        "72.2343.21212 is not a valid version, valid versions are ['4.9.10']"
    )
]


@pytest.mark.parametrize(
    "test_description, cmd_mock, namespace_mock, get_versions_mock_return_value, expected_errors",
    test_validate_version_data,
    ids=[i[0] for i in test_validate_version_data]
)
@patch('azure.cli.command_modules.aro.custom.aro_get_versions')
def test_validate_version(

    # Mocked Functions
    aro_get_versions_mock,
    # Test cases parameters:
    test_description, cmd_mock, namespace_mock, get_versions_mock_return_value, expected_errors
):
    aro_get_versions_mock.return_value = get_versions_mock_return_value

    validate_version_fn = dyn_validate_version()
    if expected_errors is None:
        errors = validate_version_fn(cmd_mock, namespace_mock)

        if (len(errors) > 0):
            raise Exception(f"Unexpected Error: {errors[0][3]}")
    else:
        errors = validate_version_fn(cmd_mock, namespace_mock)

        if (errors[0][3] != expected_errors):
            raise Exception(f"Error returned was not expected\n Expected : {expected_errors}\n Actual   : {errors[0][3]}")


test_dyn_validate_managed_identity_delete_permissions_data = [
    (
        "should not return missing permissions when actions are permitted",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(managed_identities=["/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity1"]),
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=["Microsoft.ManagedIdentity/userAssignedIdentities/delete"], not_actions=[])]}),
        {
            "resource_group": "rg",
            "name": "identity1",
            "namespace": "Microsoft.ManagedIdentity",
            "type": "userAssignedIdentities"
        },
        None
    ),
    (
        "should return missing permissions when actions are not permitted",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(managed_identities=["/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity1"]),
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=[], not_actions=["Microsoft.ManagedIdentity/userAssignedIdentities/delete"])]}),
        {
            "resource_group": "rg",
            "name": "identity1",
            "namespace": "Microsoft.ManagedIdentity",
            "type": "userAssignedIdentities"
        },
        "Microsoft.ManagedIdentity/userAssignedIdentities/delete permission is missing over /subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity1"
    ),
    (
        "should return missing permissions when actions are missing",
        Mock(cli_ctx=Mock(get_progress_controller=Mock(add=Mock(), end=Mock()))),
        Mock(managed_identities=["/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity1"]),
        Mock(**{"permissions.list_for_resource.return_value": [Permission(actions=[], not_actions=[])]}),
        {
            "resource_group": "rg",
            "name": "identity1",
            "namespace": "Microsoft.ManagedIdentity",
            "type": "userAssignedIdentities"
        },
        "Microsoft.ManagedIdentity/userAssignedIdentities/delete permission is missing over /subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity1"
    )
]


@pytest.mark.parametrize(
    "test_description, cmd_mock, namespace_mock, auth_client_mock, parse_resource_id_mock_return_value, expected_missing_perms",
    test_dyn_validate_managed_identity_delete_permissions_data,
    ids=[i[0] for i in test_dyn_validate_managed_identity_delete_permissions_data]
)
@patch("azure.cli.command_modules.aro._dynamic_validators.get_mgmt_service_client")
@patch("azure.cli.command_modules.aro._dynamic_validators.parse_resource_id")
def test_dyn_validate_managed_identity_delete_permissions(
    # Mocked functions:
    parse_resource_id_mock, get_mgmt_service_client_mock,
    # Test cases parameters:
    test_description, cmd_mock, namespace_mock, auth_client_mock, parse_resource_id_mock_return_value, expected_missing_perms
):
    parse_resource_id_mock.return_value = parse_resource_id_mock_return_value
    get_mgmt_service_client_mock.side_effect = [auth_client_mock]

    validate_fn = dyn_validate_managed_identity_delete_permissions()
    missing_perms = validate_fn(cmd_mock, namespace_mock)

    if expected_missing_perms is None:
        assert len(missing_perms) == 0, f"Unexpected errors: {missing_perms}"
    else:
        assert len(missing_perms) > 0, "Expected errors but got none"
        assert expected_missing_perms in missing_perms[0], f"Expected error '{expected_missing_perms}' but got '{missing_perms[0]}'"
