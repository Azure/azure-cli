# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class TestAAZResourceArgFmt(ScenarioTest):
    """ Scenario tests can not be contained in azure-cli-core, so have to move them here."""

    def format_arg(self, schema, data):
        from azure.cli.core.aaz._command_ctx import AAZCommandCtx
        from azure.cli.core.aaz.exceptions import AAZInvalidArgValueError
        ctx = AAZCommandCtx(
            cli_ctx=self.cli_ctx, schema=schema,
            command_args=data
        )
        ctx.format_args()
        return ctx.args

    @ResourceGroupPreparer(name_prefix='test_resource_location_arg_fmt', location="eastus2")
    def test_resource_location_arg_fmt(self, resource_group):
        from azure.cli.core.aaz._arg import AAZArgumentsSchema
        from azure.cli.core.aaz.exceptions import AAZInvalidArgValueError
        from azure.cli.core.aaz import AAZResourceGroupNameArg, AAZResourceLocationArg, AAZResourceLocationArgFormat, AAZStrArg

        schema = AAZArgumentsSchema()
        schema.rg_name = AAZResourceGroupNameArg()
        schema.location = AAZResourceLocationArg(
            fmt=AAZResourceLocationArgFormat(resource_group_arg='rg_name'),
            nullable=True
        )
        schema.name = AAZStrArg()

        args = self.format_arg(schema, {
            "rg_name": resource_group,
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "location": "eastus2"
        })

        args = self.format_arg(schema, {
            "rg_name": resource_group,
            "location": "westus"
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "location": "westus"
        })

        args = self.format_arg(schema, {
            "rg_name": resource_group,
            "location": "North Central US"
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "location": "northcentralus"
        })

        args = self.format_arg(schema, {
            "rg_name": resource_group,
            "location": None
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "location": None
        })

        args = self.format_arg(schema, {
            "name": "test"
        })
        self.assertEqual(args.to_serialized_data(), {
            "name": "test"
        })

        schema = AAZArgumentsSchema()
        schema.rg_name = AAZResourceGroupNameArg()
        schema.location = AAZResourceLocationArg()
        schema.name = AAZStrArg()

        args = self.format_arg(schema, {
            "rg_name": resource_group,
            "name": "test"
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "name": "test"
        })

        args = self.format_arg(schema, {
            "rg_name": resource_group,
            "location": "eastus",
            "name": "test"
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "location": "eastus",
            "name": "test"
        })

        args = self.format_arg(schema, {
            "rg_name": resource_group,
            "location": "South Africa North",
            "name": "test"
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "location": "southafricanorth",
            "name": "test"
        })

    @ResourceGroupPreparer(name_prefix='test_resource_id_arg_fmt', location="eastus2")
    def test_resource_id_arg_fmt(self, resource_group):
        from azure.cli.core.aaz._arg import AAZArgumentsSchema
        from azure.cli.core.aaz.exceptions import AAZInvalidArgValueError
        from azure.cli.core.aaz import AAZResourceGroupNameArg, AAZResourceLocationArg, AAZResourceIdArg, AAZStrArg, \
            AAZResourceLocationArgFormat, AAZResourceIdArgFormat, AAZObjectArg, AAZListArg
        from azure.cli.core.commands.client_factory import get_subscription_id
        sub_id = get_subscription_id(cli_ctx=self.cli_ctx)

        schema = AAZArgumentsSchema()
        schema.rg_name = AAZResourceGroupNameArg()
        schema.location = AAZResourceLocationArg(
            fmt=AAZResourceLocationArgFormat(resource_group_arg='rg_name'),
        )
        schema.vnet_name = AAZStrArg()
        schema.subnet = AAZObjectArg()
        schema.subnet.id = AAZResourceIdArg(fmt=AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{rg_name}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/locations/{location}/subnets/{}"
        ))

        schema.vnets = AAZListArg()
        schema.vnets.Element = AAZResourceIdArg(fmt=AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{rg_name}/providers/Microsoft.Network/virtualNetworks/{}"
        ), nullable=True)

        schema.vm = AAZResourceIdArg(fmt=AAZResourceIdArgFormat(
            template="/subscriptions/{}/resourceGroups/{rg_name}/providers/Microsoft.Compute/virtualMachines/{}"
        ))

        args = self.format_arg(schema, {
            "rg_name": resource_group,
            "name": "test",
            "vnet_name": "test-vnet",
            "subnet": {
                "id": "test-subnet"
            },
            "vnets": [
                "vnet1",
                f"/subscriptions/{sub_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/vnet2",
                f"/subscRiptions/{sub_id}/reSourcegroupS/{resource_group}/providers/microsoFT.network/Virtualnetworks/vnet3",
                None,
            ],
        })
        self.assertEqual(args.to_serialized_data(), {
            "rg_name": resource_group,
            "location": "eastus2",
            "vnet_name": "test-vnet",
            "subnet": {
                "id": f"/subscriptions/{sub_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/test-vnet/locations/eastus2/subnets/test-subnet"
            },
            "vnets": [
                f"/subscriptions/{sub_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/vnet1",
                f"/subscriptions/{sub_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/vnet2",
                f"/subscRiptions/{sub_id}/reSourcegroupS/{resource_group}/providers/microsoFT.network/Virtualnetworks/vnet3",
                None,
            ]
        })

        with self.assertRaises(AAZInvalidArgValueError):
            self.format_arg(schema, {
                "rg_name": resource_group,
                "name": "test",
                "vnet_name": "test-vnet",
                "subnet": {
                    "id": f"/subscriptions/{sub_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/test-subnet"
                }
            })

        with self.assertRaises(AAZInvalidArgValueError):
            self.format_arg(schema, {
                "rg_name": resource_group,
                "name": "test",
                "subnet": {
                    "id": "test-subnet"
                }
            })

        with self.assertRaises(AAZInvalidArgValueError):
            self.format_arg(schema, {
                "rg_name": resource_group,
                "name": "test",
                "vm": "test-vm"
            })

    def test_subscription_id_arg_format(self, resource_group):
        from azure.cli.core.aaz._arg import AAZArgumentsSchema
        from azure.cli.core.aaz import AAZSubscriptionIdArg, AAZSubscriptionIdArgFormat
        from azure.cli.core._profile import Profile

        sub = Profile(cli_ctx=self.cli_ctx).load_cached_subscriptions()[0]

        schema = AAZArgumentsSchema()
        schema.sub = AAZSubscriptionIdArg()

        args = self.format_arg(schema, {
            "sub": sub['name'],
        })
        self.assertEqual(args.to_serialized_data(), {
            "sub": sub['id'],
        })
