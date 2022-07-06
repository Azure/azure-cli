# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest

from azure.cli.core import azclierror
from azure.cli.core.aaz import exceptions as aazerror
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz import AAZArgumentsSchema
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.core.mock import DummyCli


class TestAAZArgBaseFmt(unittest.TestCase):

    @staticmethod
    def format_arg(schema, data):
        ctx = AAZCommandCtx(
            cli_ctx=DummyCli(), schema=schema,
            command_args=data
        )
        ctx.format_args()
        return ctx.args

    def test_str_fmt(self):
        from azure.cli.core.aaz import AAZStrArg, AAZStrArgFormat
        schema = AAZArgumentsSchema()
        schema.str1 = AAZStrArg(
            fmt=AAZStrArgFormat(
                pattern="[a-z]+",
                max_length=8,
                min_length=2,
            ),
            nullable=True
        )

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": ""})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": "1234"})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": "abcdefghi"})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": "aBCD"})

        args = self.format_arg(schema, {"str1": "abcdefgh"})
        self.assertEqual(args.str1, "abcdefgh")

        args = self.format_arg(schema, {"str1": "abcd"})
        self.assertEqual(args.str1, "abcd")

        args = self.format_arg(schema, {"str1": None})
        self.assertEqual(args.str1, None)

    def test_int_fmt(self):
        from azure.cli.core.aaz import AAZIntArg, AAZIntArgFormat

        schema = AAZArgumentsSchema()
        schema.int1 = AAZIntArg(
            fmt=AAZIntArgFormat(
                multiple_of=10,
                maximum=30,
                minimum=20,
            ),
            nullable=True
        )

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"int1": 10})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"int1": 25})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"int1": 40})

        args = self.format_arg(schema, {"int1": 20})
        self.assertEqual(args.int1, 20)

        args = self.format_arg(schema, {"int1": 30})
        self.assertEqual(args.int1, 30)

        args = self.format_arg(schema, {"int1": None})
        self.assertEqual(args.int1, None)

    def test_float_fmt(self):
        from azure.cli.core.aaz import AAZFloatArg, AAZFloatArgFormat

        schema = AAZArgumentsSchema()
        schema.flt1 = AAZFloatArg(
            fmt=AAZFloatArgFormat(
                multiple_of=1.1,
                maximum=33,
                minimum=22,
                exclusive_maximum=True,
                exclusive_minimum=True,
            )
        )

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 1.1})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 22})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 33})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 23})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 23.099})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 31.901})

        args = self.format_arg(schema, {"flt1": 23.1})
        self.assertEqual(args.flt1, 23.1)

        args = self.format_arg(schema, {"flt1": 31.9})
        self.assertEqual(args.flt1, 31.9)

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 22.0000000001})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"flt1": 32.9999999999})

        schema = AAZArgumentsSchema()
        schema.flt1 = AAZFloatArg(
            fmt=AAZFloatArgFormat(
                multiple_of=1.1,
                maximum=33,
                minimum=22,
                exclusive_maximum=False,
                exclusive_minimum=False,
            ),
            nullable=True
        )
        args = self.format_arg(schema, {"flt1": 22.0000000001})
        self.assertEqual(args.flt1, 22)

        args = self.format_arg(schema, {"flt1": 32.9999999999})
        self.assertEqual(args.flt1, 33)

        args = self.format_arg(schema, {"flt1": None})
        self.assertEqual(args.flt1, None)

    def test_bool_fmt(self):
        from azure.cli.core.aaz import AAZBoolArg, AAZBoolArgFormat

        schema = AAZArgumentsSchema()
        schema.bool = AAZBoolArg(
            fmt=AAZBoolArgFormat(reverse=True),
            nullable=True,
        )

        args = self.format_arg(schema, {"bool": True})
        self.assertEqual(args.bool, False)

        args = self.format_arg(schema, {"bool": False})
        self.assertEqual(args.bool, True)

        args = self.format_arg(schema, {"bool": None})
        self.assertEqual(args.bool, None)

    def test_object_fmt(self):
        from azure.cli.core.aaz import AAZObjectArgFormat, AAZStrArgFormat, AAZBoolArgFormat, AAZIntArgFormat, \
            AAZDictArgFormat, AAZListArgFormat, AAZFloatArgFormat
        from azure.cli.core.aaz import AAZObjectArg, AAZStrArg, AAZBoolArg, AAZIntArg, AAZDictArg, AAZListArg, \
            AAZFloatArg

        schema = AAZArgumentsSchema()
        schema.properties = AAZObjectArg(fmt=AAZObjectArgFormat(
            max_properties=3,
            min_properties=2,
        ))
        schema.properties.name = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z]+'))
        schema.properties.enabled = AAZBoolArg(fmt=AAZBoolArgFormat(reverse=True))
        schema.properties.count = AAZIntArg(fmt=AAZIntArgFormat(minimum=0))
        schema.properties.vnet = AAZObjectArg()
        schema.properties.vnet.name = AAZStrArg()
        schema.properties.vnet.name2 = AAZStrArg()

        args = self.format_arg(schema, {
            "properties": {
                "name": "abcd",
                "enabled": True,
                "count": 100
            }
        })
        self.assertEqual(args.properties.to_serialized_data(), {
            "name": "abcd",
            "enabled": False,
            "count": 100
        })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "properties": {
                    "name": "abcd",
                }
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "properties": {
                    "name": "abcd",
                    "enabled": False,
                    "count": 100,
                    "vnet": {
                        "name": "test",
                    }
                }
            })

        schema = AAZArgumentsSchema()
        schema.properties = AAZObjectArg(nullable=True)
        schema.properties.name = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z]+'))
        schema.properties.enabled = AAZBoolArg(fmt=AAZBoolArgFormat(reverse=True))
        schema.properties.count = AAZIntArg(fmt=AAZIntArgFormat(minimum=0))
        schema.properties.vnet = AAZObjectArg(nullable=True)
        schema.properties.vnet.name = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z]+'))

        schema.properties.tags = AAZDictArg(fmt=AAZDictArgFormat())
        schema.properties.tags.Element = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z]+'))
        schema.properties.actions = AAZListArg(fmt=AAZListArgFormat())
        schema.properties.actions.Element = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z]+'))
        schema.properties.sub = AAZObjectArg(fmt=AAZObjectArgFormat())
        schema.properties.name2 = AAZStrArg(fmt=AAZStrArgFormat())
        schema.properties.int2 = AAZIntArg(fmt=AAZIntArgFormat())
        schema.properties.bool2 = AAZBoolArg(fmt=AAZBoolArgFormat())
        schema.properties.float2 = AAZFloatArg(fmt=AAZFloatArgFormat())

        args = self.format_arg(schema, {
            "properties": {}
        })
        self.assertEqual(args.properties.to_serialized_data(), {})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "properties": {
                    "name": "a1234",
                }
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "properties": {
                    "count": -10,
                }
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "properties": {
                    "vnet": {
                        "name": "test11",
                    }
                }
            })

        args = self.format_arg(schema, {"properties": None})
        self.assertEqual(args.properties, None)

        args = self.format_arg(schema, {
            "properties": {
                "vnet": None
            }
        })
        self.assertEqual(args, {
            "properties": {
                "vnet": None
            }
        })

    def test_dict_fmt(self):
        from azure.cli.core.aaz import AAZObjectArgFormat, AAZDictArgFormat, AAZStrArgFormat, AAZIntArgFormat
        from azure.cli.core.aaz import AAZObjectArg, AAZDictArg, AAZStrArg, AAZIntArg

        schema = AAZArgumentsSchema()
        schema.tags = AAZDictArg(fmt=AAZDictArgFormat(max_properties=3, min_properties=2), nullable=True)
        schema.tags.Element = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z0-9]+'))
        schema.actions = AAZDictArg()
        schema.actions.Element = AAZObjectArg(nullable=True)
        schema.actions.Element.name = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z]+'))
        schema.actions.Element.name2 = AAZStrArg(nullable=True)

        args = self.format_arg(schema, {
            "tags": {
                "flag1": "v1",
                "flag2": "v2",
            },
            "actions": {
                "a": {
                    "name": "abc"
                },
                "b": {
                    "name": "c"
                }
            }
        })
        self.assertEqual(args.to_serialized_data(), {
            "tags": {
                "flag1": "v1",
                "flag2": "v2",
            },
            "actions": {
                "a": {
                    "name": "abc"
                },
                "b": {
                    "name": "c"
                }
            }
        })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "tags": {
                    "flag1": "v1",
                },
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "tags": {
                    "flag1": "v1",
                    "flag2": "v2",
                    "flag3": "v3",
                    "flag4": "v4",
                },
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "actions": {
                    "a": {
                        "name": "abc11"
                    },
                },
            })

        args = self.format_arg(schema, {
            "tags": None,
            "actions": {
                "a": {
                    "name": "abc"
                },
                "b": {
                    "name": "c",
                    "name2": None,
                },
                "c": None
            }
        })
        self.assertEqual(args.to_serialized_data(), {
            "tags": None,
            "actions": {
                "a": {
                    "name": "abc"
                },
                "b": {
                    "name": "c",
                    "name2": None,
                },
                "c": None
            }
        })

    def test_list_fmt(self):
        from azure.cli.core.aaz import AAZObjectArgFormat, AAZListArgFormat, AAZStrArgFormat, AAZIntArgFormat
        from azure.cli.core.aaz import AAZObjectArg, AAZListArg, AAZStrArg, AAZIntArg

        schema = AAZArgumentsSchema()
        schema.tags = AAZListArg(fmt=AAZListArgFormat(unique=True, max_length=3, min_length=2))
        schema.tags.Element = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z0-9]+'), nullable=True)
        schema.actions = AAZListArg(nullable=True)
        schema.actions.Element = AAZObjectArg()
        schema.actions.Element.name = AAZStrArg(fmt=AAZStrArgFormat(pattern='[a-z]+'))

        args = self.format_arg(schema, {
            "tags": ['v1', 'v2'],
            "actions": [
                {
                    "name": "abc"
                },
                {
                    "name": "c"
                }
            ]
        })
        self.assertEqual(args.to_serialized_data(), {
            "tags": ['v1', 'v2'],
            "actions": [
                {
                    "name": "abc"
                },
                {
                    "name": "c"
                }
            ]
        })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "tags": ['v1',],
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "tags": ['v1', 'v2', 'v3', 'v4'],
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "tags": ['v1', 'v2', 'v2'],
            })

        args = self.format_arg(schema, {
            "tags": ['v1', 'v2'],
        })
        self.assertEqual(args.to_serialized_data(), {
            "tags": ['v1', 'v2'],
        })

        args = self.format_arg(schema, {
            "tags": ['v1', 'v2', None],
            "actions": None,
        })
        self.assertEqual(args.to_serialized_data(), {
            "tags": ['v1', 'v2', None],
            "actions": None,
        })

class TestAAZArgResourceFmt(ScenarioTest):

    def format_arg(self, schema, data):
        ctx = AAZCommandCtx(
            cli_ctx=self.cli_ctx, schema=schema,
            command_args=data
        )
        ctx.format_args()
        return ctx.args

    @ResourceGroupPreparer(name_prefix='test_resource_location_arg_fmt', location="eastus2")
    def test_resource_location_arg_fmt(self, resource_group):
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

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "rg_name": resource_group,
                "name": "test",
                "vnet_name": "test-vnet",
                "subnet": {
                    "id": f"/subscriptions/{sub_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/test-vnet/subnets/test-subnet"
                }
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "rg_name": resource_group,
                "name": "test",
                "subnet": {
                    "id": "test-subnet"
                }
            })

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {
                "rg_name": resource_group,
                "name": "test",
                "vm": "test-vm"
            })

    def test_subscription_id_arg_format(self):
        from azure.cli.core.aaz import AAZSubscriptionIdArg, AAZSubscriptionIdArgFormat
        from azure.cli.core._profile import Profile

        sub = Profile(cli_ctx=self.cli_ctx).get_subscription()

        schema = AAZArgumentsSchema()
        schema.sub = AAZSubscriptionIdArg()

        args = self.format_arg(schema, {
            "sub": sub['name'],
        })
        self.assertEqual(args.to_serialized_data(), {
            "sub": sub['id'],
        })
