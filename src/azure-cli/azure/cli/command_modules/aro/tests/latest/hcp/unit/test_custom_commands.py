# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import types
import unittest
from unittest import mock

from azure.cli.core.aaz._field_value import AAZObject
from azure.cli.core.azclierror import InvalidArgumentValueError, MutuallyExclusiveArgumentError

from azure.cli.command_modules.aro.azext_aro_hcp.custom import ClusterCreate, ClusterUpdate, GetVersions, RequestCredential


SUBNET_ID = ("/subscriptions/000/resourceGroups/network-rg/providers/Microsoft.Network/"
             "virtualNetworks/vnet/subnets/cluster-subnet")


def _identity_id(name):
    return ("/subscriptions/000/resourceGroups/network-rg/providers/"
            "Microsoft.ManagedIdentity/userAssignedIdentities/{}".format(name))


class _Arg:
    def __init__(self, value):
        self.value = value

    def __iter__(self):
        return iter(self.value)

    def to_serialized_data(self):
        return self.value


class _OperatorIdentity:
    def __init__(self, name, resource_id):
        self.name = _Arg(name)
        self.resource_id = _Arg(resource_id)


class ClusterCreateTest(unittest.TestCase):

    def test_help_examples_use_custom_identity_arguments(self):
        example_text = " ".join(example["text"] for example in ClusterCreate.AZ_HELP["examples"])

        self.assertIn("--assign-control-plane-operator-identity", example_text)
        self.assertIn("--assign-data-plane-operator-identity", example_text)
        self.assertIn("--assign-service-managed-identity", example_text)
        self.assertNotIn("--etcd-encryption-type", example_text)
        self.assertIn("--key-management-mode CustomerManaged", example_text)
        self.assertNotIn("--control-plane-operators", example_text)
        self.assertNotIn("--data-plane-operators", example_text)
        self.assertEqual(9, example_text.count("--assign-control-plane-operator-identity"))
        self.assertEqual(3, example_text.count("--assign-data-plane-operator-identity"))

    def test_key_management_mode_is_required_without_default(self):
        schema = ClusterCreate._build_arguments_schema()

        self.assertTrue(schema.key_management_mode._required)
        self.assertIsNone(schema.key_management_mode._default)

    @staticmethod
    def _identity_parser():
        schema = ClusterCreate._build_arguments_schema()
        command_arg = schema.assign_control_plane_operator_identity.to_cmd_arg(
            "assign_control_plane_operator_identity"
        )
        settings = command_arg.type.settings
        parser = argparse.ArgumentParser()
        parser.add_argument(
            *command_arg.options_list,
            dest="identities",
            nargs=settings["nargs"],
            action=settings["action"],
        )
        return parser, schema

    def _command(self, control_plane, data_plane, service, container_registry=None):
        command = object.__new__(ClusterCreate)
        command.ctx = types.SimpleNamespace(args=types.SimpleNamespace(
            subnet_id=_Arg(SUBNET_ID),
            assign_control_plane_operator_identity=control_plane,
            assign_data_plane_operator_identity=data_plane,
            assign_service_managed_identity=_Arg(service),
            assign_container_registry_managed_identity=_Arg(container_registry),
            container_registry_managed_identity=_Arg(None),
        ))
        return command

    @mock.patch(
        "azure.cli.command_modules.aro.azext_aro_hcp.custom.has_value",
        side_effect=lambda arg: arg.to_serialized_data() is not None,
    )
    def test_pre_operations_maps_operator_identities(self, _):
        service = "/subscriptions/000/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/service"
        control_plane_id = "/subscriptions/000/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/control"
        data_plane_id = "/subscriptions/000/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/data"
        command = self._command(
            [_OperatorIdentity("control-plane", control_plane_id)],
            [_OperatorIdentity("disk-csi-driver", data_plane_id)],
            service,
        )

        command.pre_operations()

        args = command.ctx.args
        self.assertEqual(
            {control_plane_id: {}, service: {}},
            args.user_assigned_identities,
        )
        self.assertEqual({
            "user_assigned_identities": {
                "control_plane_operators": {"control-plane": control_plane_id},
                "data_plane_operators": {"disk-csi-driver": data_plane_id},
                "service_managed_identity": service,
            }
        }, args.operators_authentication)

    @mock.patch(
        "azure.cli.command_modules.aro.azext_aro_hcp.custom.has_value",
        side_effect=lambda arg: arg.to_serialized_data() is not None,
    )
    def test_pre_operations_resolves_all_identity_names_from_subnet(self, _):
        command = self._command(
            [_OperatorIdentity("control-plane", "control")],
            [_OperatorIdentity("disk-csi-driver", "data")],
            "service",
            "registry",
        )

        command.pre_operations()

        args = command.ctx.args
        self.assertEqual({
            _identity_id("control"): {},
            _identity_id("service"): {},
        }, args.user_assigned_identities)
        self.assertEqual({
            "user_assigned_identities": {
                "control_plane_operators": {"control-plane": _identity_id("control")},
                "data_plane_operators": {"disk-csi-driver": _identity_id("data")},
                "service_managed_identity": _identity_id("service"),
            }
        }, args.operators_authentication)
        self.assertEqual(
            _identity_id("registry"),
            args.container_registry_managed_identity,
        )

    def test_container_registry_identity_replaces_generated_argument(self):
        schema = ClusterCreate._build_arguments_schema()
        command_arg = schema.assign_container_registry_managed_identity.to_cmd_arg(
            "assign_container_registry_managed_identity"
        )

        self.assertFalse(schema.container_registry_managed_identity._registered)
        self.assertEqual(
            [
                "--registry-identity",
                "--assign-container-registry-managed-identity",
            ],
            command_arg.options_list,
        )

    def test_pre_operations_rejects_duplicate_name(self):
        command = self._command(
            [
                _OperatorIdentity("control-plane", "identity-one"),
                _OperatorIdentity("control-plane", "identity-two"),
            ],
            [_OperatorIdentity("disk-csi-driver", "identity-three")],
            "service-identity",
        )

        with self.assertRaisesRegex(InvalidArgumentValueError, "Duplicate name 'control-plane'"):
            command.pre_operations()

    def test_identity_argument_accepts_repeated_positional_pairs(self):
        parser, schema = self._identity_parser()
        namespace = parser.parse_args([
            "--control-plane-identity", "control-plane", "identity-one",
            "--control-plane-identity", "ingress", "identity-two",
        ])
        values = schema()
        namespace.identities.apply(values, "assign_control_plane_operator_identity")

        self.assertEqual([
            {"name": "control-plane", "resource_id": "identity-one"},
            {"name": "ingress", "resource_id": "identity-two"},
        ], values.assign_control_plane_operator_identity.to_serialized_data())

    def test_identity_argument_help_omits_structured_input_formats(self):
        schema = ClusterCreate._build_arguments_schema()
        command_arg = schema.assign_control_plane_operator_identity.to_cmd_arg(
            "assign_control_plane_operator_identity"
        )
        help_text = command_arg.type.settings["help"]

        self.assertIn(
            "Usage: --assign-control-plane-operator-identity OPERATOR_NAME IDENTITY",
            help_text,
        )
        self.assertNotIn("shorthand-syntax", help_text)
        self.assertNotIn("json-file", help_text)
        self.assertNotIn('Try "??"', help_text)

    def test_identity_argument_requires_exactly_two_values(self):
        parser, _ = self._identity_parser()

        with self.assertRaisesRegex(InvalidArgumentValueError, "expects OPERATOR_NAME IDENTITY"):
            parser.parse_args([
                "--assign-control-plane-operator-identity", "control-plane",
            ])

    def test_content_adds_identity(self):
        operation_type = ClusterCreate.HcpOpenShiftClustersCreateOrUpdate
        base_type = operation_type.__mro__[1]
        operation = object.__new__(operation_type)

        with mock.patch.object(
                base_type, "content", new_callable=mock.PropertyMock,
                return_value={"properties": {}}):
            self.assertEqual(
                {"properties": {}, "identity": {"type": "UserAssigned"}},
                operation.content,
            )

    def test_content_replaces_identity_type(self):
        operation_type = ClusterCreate.HcpOpenShiftClustersCreateOrUpdate
        base_type = operation_type.__mro__[1]
        operation = object.__new__(operation_type)
        content = {"identity": {"type": "SystemAssigned", "userAssignedIdentities": {}}}

        with mock.patch.object(
                base_type, "content", new_callable=mock.PropertyMock,
                return_value=content):
            self.assertEqual("UserAssigned", operation.content["identity"]["type"])
            self.assertEqual({}, operation.content["identity"]["userAssignedIdentities"])


class ClusterUpdateTest(unittest.TestCase):

    def test_help_examples_use_custom_identity_arguments(self):
        example_text = " ".join(example["text"] for example in ClusterUpdate.AZ_HELP["examples"])

        self.assertIn("--assign-control-plane-operator-identity", example_text)
        self.assertIn("--assign-data-plane-operator-identity", example_text)
        self.assertIn("--assign-service-managed-identity", example_text)

    @staticmethod
    def _command(control_plane=None, data_plane=None, service=None, container_registry=None):
        command = object.__new__(ClusterUpdate)
        args = ClusterUpdate._build_arguments_schema()()
        for name, value in (
            ("assign_control_plane_operator_identity", control_plane),
            ("assign_data_plane_operator_identity", data_plane),
            ("assign_service_managed_identity", service),
            ("assign_container_registry_managed_identity", container_registry),
        ):
            if value is not None:
                args[name] = value
        command.ctx = types.SimpleNamespace(args=args, get_http_client=mock.Mock())
        return command

    @staticmethod
    def _instance():
        schema = ClusterUpdate.HcpOpenShiftClustersGet._build_schema_on_200()
        data = {
            "location": "eastus",
            "identity": {
                "type": "UserAssigned",
                "userAssignedIdentities": {
                    _identity_id("control"): {},
                    _identity_id("data"): {},
                    _identity_id("service"): {},
                },
            },
            "properties": {
                "version": {"id": "4.19", "channelGroup": "stable"},
                "platform": {
                    "subnetId": SUBNET_ID,
                    "vnetIntegrationSubnetId": SUBNET_ID,
                    "networkSecurityGroupId": (
                        "/subscriptions/000/resourceGroups/network-rg/providers/"
                        "Microsoft.Network/networkSecurityGroups/cluster-nsg"
                    ),
                    "containerRegistry": {"managedIdentity": _identity_id("registry")},
                    "operatorsAuthentication": {
                        "userAssignedIdentities": {
                            "controlPlaneOperators": {"existing-control": _identity_id("control")},
                            "dataPlaneOperators": {"existing-data": _identity_id("data")},
                            "serviceManagedIdentity": _identity_id("service"),
                        },
                    },
                },
            },
        }
        return AAZObject(schema, data=schema.process_data(data))

    def test_pre_instance_update_replaces_supplied_category_and_rebuilds_top_level_identities(self):
        instance = self._instance()
        command = self._command(
            control_plane=[{"name": "new-control", "resource_id": "new-control-identity"}],
        )

        command.pre_instance_update(instance)

        operator_identities = instance.properties.platform.operators_authentication.user_assigned_identities
        self.assertEqual({"new-control": _identity_id("new-control-identity")},
                         operator_identities.control_plane_operators)
        self.assertEqual({"existing-data": _identity_id("data")}, operator_identities.data_plane_operators)
        self.assertEqual(_identity_id("service"), operator_identities.service_managed_identity)
        self.assertEqual({
            _identity_id("new-control-identity"): {},
            _identity_id("data"): {},
            _identity_id("service"): {},
        }, instance.identity.user_assigned_identities.to_serialized_data())

    def test_pre_instance_update_resolves_all_identity_names_from_subnet(self):
        instance = self._instance()
        command = self._command(
            control_plane=[{"name": "new-control", "resource_id": "control-two"}],
            data_plane=[{"name": "new-data", "resource_id": "data-two"}],
            service="service-two",
        )

        command.pre_instance_update(instance)

        operator_identities = instance.properties.platform.operators_authentication.user_assigned_identities
        self.assertEqual({"new-control": _identity_id("control-two")},
                         operator_identities.control_plane_operators)
        self.assertEqual({"new-data": _identity_id("data-two")},
                         operator_identities.data_plane_operators)
        self.assertEqual(_identity_id("service-two"), operator_identities.service_managed_identity)
        self.assertEqual({
            _identity_id("control-two"): {},
            _identity_id("data-two"): {},
            _identity_id("service-two"): {},
        }, instance.identity.user_assigned_identities.to_serialized_data())

    def test_pre_instance_update_preserves_container_registry_identity_resource_id(self):
        registry_id = _identity_id("registry")
        command = self._command(container_registry=registry_id)

        command.pre_instance_update(self._instance())

        self.assertEqual(
            registry_id,
            command.ctx.args.container_registry_managed_identity,
        )

    def test_container_registry_identity_replaces_generated_argument(self):
        schema = ClusterUpdate._build_arguments_schema()
        command_arg = schema.assign_container_registry_managed_identity.to_cmd_arg(
            "assign_container_registry_managed_identity"
        )

        self.assertFalse(schema.container_registry_managed_identity._registered)
        self.assertEqual(
            [
                "--registry-identity",
                "--assign-container-registry-managed-identity",
            ],
            command_arg.options_list,
        )

    def test_pre_instance_update_preserves_identities_when_arguments_are_omitted(self):
        instance = self._instance()
        command = self._command()

        command.pre_instance_update(instance)

        self.assertEqual(
            {
                _identity_id("control"): {},
                _identity_id("data"): {},
                _identity_id("service"): {},
            },
            instance.identity.user_assigned_identities.to_serialized_data(),
        )
        operator_identities = instance.properties.platform.operators_authentication.user_assigned_identities
        self.assertEqual({"existing-control": _identity_id("control")},
                         operator_identities.control_plane_operators)
        self.assertEqual({"existing-data": _identity_id("data")}, operator_identities.data_plane_operators)
        self.assertEqual(_identity_id("service"), operator_identities.service_managed_identity)

    def test_pre_instance_update_identity_flags_produce_put_content(self):
        for flag, field in (
            ("control_plane", "controlPlaneOperators"),
            ("data_plane", "dataPlaneOperators"),
            ("service", "serviceManagedIdentity"),
            ("container_registry", None),
        ):
            for use_resource_id in (False, True):
                with self.subTest(flag=flag, use_resource_id=use_resource_id):
                    instance = self._instance()
                    expected = instance.to_serialized_data()
                    identity = _identity_id("replacement") if use_resource_id else "replacement"
                    value = [{"name": "replacement", "resource_id": identity}] if flag in (
                        "control_plane", "data_plane",
                    ) else identity
                    command = self._command(**{flag: value})
                    command.ctx.vars = types.SimpleNamespace(instance=instance)
                    platform = expected["properties"]["platform"]
                    operators = platform["operatorsAuthentication"]["userAssignedIdentities"]
                    if field is None:
                        platform["containerRegistry"]["managedIdentity"] = _identity_id("replacement")
                    else:
                        operators[field] = (
                            {"replacement": _identity_id("replacement")}
                            if flag in ("control_plane", "data_plane") else _identity_id("replacement")
                        )
                        assigned_ids = set(operators["controlPlaneOperators"].values())
                        assigned_ids.update(operators["dataPlaneOperators"].values())
                        assigned_ids.add(operators["serviceManagedIdentity"])
                        expected["identity"]["userAssignedIdentities"] = {
                            identity_id: {} for identity_id in assigned_ids
                        }

                    command.pre_instance_update(instance)
                    command.InstanceUpdateByJson(ctx=command.ctx)()
                    operation = command.HcpOpenShiftClustersCreateOrUpdate(ctx=command.ctx)

                    self.assertEqual("PUT", operation.method)
                    self.assertEqual(expected, operation.content)

    def test_pre_instance_update_rejects_duplicate_name(self):
        command = self._command(control_plane=[
            {"name": "control-plane", "resource_id": "identity-one"},
            {"name": "control-plane", "resource_id": "identity-two"},
        ])

        with self.assertRaisesRegex(InvalidArgumentValueError, "Duplicate name 'control-plane'"):
            command.pre_instance_update(self._instance())


class GetVersionsTest(unittest.TestCase):

    def _command(self, control_plane=False, node_pools=False):
        command = object.__new__(GetVersions)
        command.ctx = types.SimpleNamespace(args=types.SimpleNamespace(
            control_plane=_Arg(control_plane),
            node_pools=_Arg(node_pools),
        ))
        return command

    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.has_value", return_value=True)
    @mock.patch.object(GetVersions.__mro__[1], "_output")
    def test_default_output_filters_and_sorts_full_versions(self, base_output, _):
        base_output.return_value = ([
            {"name": "4.20.1", "properties": {"enabled": True, "channelGroup": "candidate"}},
            {"name": "4.19.3", "properties": {"enabled": False}},
            {"name": "4.19.2", "properties": {"channelGroup": "stable"}},
        ], "next")

        result, next_link = self._command()._output()

        self.assertEqual(["4.19.2", "4.20.1"], [row["Name"] for row in result])
        self.assertEqual("next", next_link)

    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.has_value", return_value=True)
    @mock.patch.object(GetVersions.__mro__[1], "_output")
    def test_control_plane_output_deduplicates_major_minor(self, base_output, _):
        base_output.return_value = ([
            {"name": "4.20.2", "properties": {"channelGroup": "stable"}},
            {"name": "4.19.3", "properties": {"channelGroup": "stable"}},
            {"name": "4.20.1", "properties": {"channelGroup": "candidate"}},
            {"name": "invalid", "properties": {}},
        ], None)

        result, _ = self._command(control_plane=True)._output()

        self.assertEqual(["4.19", "4.20"], [row["Name"] for row in result])
        self.assertEqual(["stable", "candidate"], [row["ChannelGroup"] for row in result])

    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.has_value", return_value=True)
    @mock.patch.object(GetVersions.__mro__[1], "_output", return_value=([], None))
    def test_flags_are_mutually_exclusive(self, _, __):
        with self.assertRaises(MutuallyExclusiveArgumentError):
            self._command(control_plane=True, node_pools=True)._output()


class RequestCredentialTest(unittest.TestCase):

    def test_no_wait_is_disabled(self):
        schema = RequestCredential._build_arguments_schema()

        self.assertFalse(RequestCredential.AZ_SUPPORT_NO_WAIT)
        self.assertFalse(schema.no_wait._registered)
        self.assertIs(schema.no_wait._default, False)

    def test_handler_without_admin_raises_invalid_argument_value_error(self):
        command = object.__new__(RequestCredential)
        with self.assertRaisesRegex(
                InvalidArgumentValueError,
                "Requesting a non-admin credential is not supported yet"):
            command._handler({"admin": False})

    @mock.patch(
        "azure.cli.command_modules.aro.azext_aro_hcp._kubeconfig._generate_admin_credential_request",
        return_value=(b"private-key", "csr"),
    )
    @mock.patch.object(RequestCredential.__mro__[1], "_handler", return_value="poller")
    def test_handler_populates_internal_csr(self, base_handler, _):
        command = object.__new__(RequestCredential)
        command_args = {"admin": True}

        self.assertEqual("poller", command._handler(command_args))

        self.assertEqual("csr", command_args["certificate_signing_request"])
        self.assertEqual(b"private-key", command._private_key_pem)
        base_handler.assert_called_once_with(command_args)

    @mock.patch(
        "azure.cli.command_modules.aro.azext_aro_hcp._kubeconfig._generate_admin_credential_request",
        return_value=(b"private-key", "csr"),
    )
    @mock.patch.object(RequestCredential.__mro__[1], "_handler", side_effect=RuntimeError("failed"))
    def test_handler_clears_key_when_poller_creation_fails(self, _, __):
        command = object.__new__(RequestCredential)
        with self.assertRaisesRegex(RuntimeError, "failed"):
            command._handler({"admin": True})
        self.assertFalse(hasattr(command, "_private_key_pem"))

    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp._kubeconfig.print_or_merge_credentials")
    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp._kubeconfig._embed_private_key", return_value="embedded")
    @mock.patch.object(RequestCredential, "deserialize_output", return_value={"kubeconfig": "config\\n"})
    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.has_value", return_value=False)
    def test_output_embeds_key_and_uses_default_context(
            self, _, __, embed_private_key, print_or_merge):
        command = object.__new__(RequestCredential)
        command._private_key_pem = b"private-key"
        command.ctx = types.SimpleNamespace(
            vars=types.SimpleNamespace(instance=object()),
            args=types.SimpleNamespace(
                file=_Arg("/tmp/config"),
                context_name=_Arg(None),
                name=_Arg("cluster-one"),
                resource_group=_Arg("group-one"),
                overwrite_existing=_Arg(False),
            ),
        )

        self.assertIsNone(command._output())

        self.assertFalse(hasattr(command, "_private_key_pem"))
        embed_private_key.assert_called_once_with("config\n", b"private-key", "group-one-cluster-one-admin")
        print_or_merge.assert_called_once_with(
            "/tmp/config", "embedded", False, "cluster-one-admin"
        )

    def test_hidden_csr_is_added_to_request_content(self):
        operation_type = RequestCredential.HcpOpenShiftClustersRequestAdminCredential
        base_type = operation_type.__mro__[1]
        operation = object.__new__(operation_type)
        operation.ctx = types.SimpleNamespace(
            args=types.SimpleNamespace(certificate_signing_request=_Arg("pem-csr"))
        )

        with mock.patch.object(
                base_type, "content", new_callable=mock.PropertyMock, return_value={}):
            self.assertEqual(
                {"certificateSigningRequest": "pem-csr"},
                operation.content,
            )


if __name__ == "__main__":
    unittest.main()
