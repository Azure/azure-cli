# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import base64
import json
import random
import unittest

from azure.cli.core import azclierror
from azure.cli.core.aaz import exceptions as aazerror
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz import AAZArgumentsSchema
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

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"str1": ""})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"str1": "1234"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"str1": "abcdefghi"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"str1": "aBCD"})

        args = self.format_arg(schema, {"str1": "abcdefgh"})
        self.assertEqual(args.str1, "abcdefgh")

        args = self.format_arg(schema, {"str1": "abcd"})
        self.assertEqual(args.str1, "abcd")

        args = self.format_arg(schema, {"str1": None})
        self.assertEqual(args.str1, None)

    def test_duration_fmt(self):
        from azure.cli.core.aaz import AAZDurationArg, AAZDurationFormat
        schema = AAZArgumentsSchema()
        schema.duration = AAZDurationArg(
            nullable=True
        )

        args = self.format_arg(schema, {"duration": "1s"})
        self.assertEqual(args.duration, "PT1S")

        args = self.format_arg(schema, {"duration": "1m"})
        self.assertEqual(args.duration, "PT1M")

        args = self.format_arg(schema, {"duration": "1h"})
        self.assertEqual(args.duration, "PT1H")

        args = self.format_arg(schema, {"duration": "1d"})
        self.assertEqual(args.duration, "P1D")

        args = self.format_arg(schema, {"duration": "0h1s"})
        self.assertEqual(args.duration, "PT1S")

        args = self.format_arg(schema, {"duration": "1dt1h1m1s"})
        self.assertEqual(args.duration, "P1DT1H1M1S")

        args = self.format_arg(schema, {"duration": "pt1h"})
        self.assertEqual(args.duration, "PT1H")

        args = self.format_arg(schema, {"duration": "p1yt1h"})
        self.assertEqual(args.duration, "P1YT1H")

        args = self.format_arg(schema, {"duration": "p1y"})
        self.assertEqual(args.duration, "P1Y")

        args = self.format_arg(schema, {"duration": "p1m"})
        self.assertEqual(args.duration, "P1M")

        args = self.format_arg(schema, {"duration": "P1Y1M100DT1h1s"})
        self.assertEqual(args.duration, "P1Y1M100DT1H1S")

        args = self.format_arg(schema, {"duration": None})
        self.assertEqual(args.duration, None)

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"duration": "1m1d"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"duration": "1x"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"duration": "-1m"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"duration": "m1s"})

    def test_date_fmt(self):
        from azure.cli.core.aaz import AAZDateArg, AAZDateFormat
        schema = AAZArgumentsSchema()
        schema.date = AAZDateArg(
            nullable=True
        )

        args = self.format_arg(schema, {"date": "2010-01-02 01:11:11 +02:00"})
        self.assertEqual(args.date, "2010-01-02")

        args = self.format_arg(schema, {"date": "2010/01/02"})
        self.assertEqual(args.date, "2010-01-02")

        args = self.format_arg(schema, {"date": "October 1 1989"})
        self.assertEqual(args.date, "1989-10-01")

        args = self.format_arg(schema, {"date": "2010/01/02 01:11:11"})
        self.assertEqual(args.date, "2010-01-02")

        args = self.format_arg(schema, {"date": None})
        self.assertEqual(args.date, None)

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            args = self.format_arg(schema, {"date": "aaaa"})

    def test_time_fmt(self):
        from azure.cli.core.aaz import AAZTimeArg, AAZTimeFormat
        schema = AAZArgumentsSchema()
        schema.time = AAZTimeArg(
            nullable=True
        )

        args = self.format_arg(schema, {"time": "2010-01-02 01:11:11.12345678 +01:00"})
        self.assertEqual(args.time, "01:11:11.123456")

        args = self.format_arg(schema, {"time": "01:11:11.0001"})
        self.assertEqual(args.time, "01:11:11.0001")

        args = self.format_arg(schema, {"time": "21:11:11.1"})
        self.assertEqual(args.time, "21:11:11.100")

        args = self.format_arg(schema, {"time": "21:01:51.00"})
        self.assertEqual(args.time, "21:01:51")

        args = self.format_arg(schema, {"time": None})
        self.assertEqual(args.time, None)

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"time": "21:01:151.00"})

    def test_datetime_fmt(self):
        from azure.cli.core.aaz import AAZDateTimeArg, AAZDateTimeFormat
        schema = AAZArgumentsSchema()
        schema.datetime = AAZDateTimeArg(
            nullable=True
        )
        schema.rfc = AAZDateTimeArg(
            fmt=AAZDateTimeFormat(protocol='rfc'),
            nullable=True
        )

        args = self.format_arg(schema, {
            "datetime": "2010-01-02 01:11:11.12345678 -06:30",
            "rfc": "2010-01-02 01:11:11.12345678 -06:30",
        })
        self.assertEqual(args.datetime, "2010-01-02T07:41:11.123456Z")
        self.assertEqual(args.rfc, "Sat, 02 Jan 2010 07:41:11 GMT")

        args = self.format_arg(schema, {
            "datetime": "Sat, 02 Jan 2010 07:41:11 GMT",
            "rfc": "2010-01-02T07:41:11.123456Z",
        })
        self.assertEqual(args.datetime, "2010-01-02T07:41:11.000Z")
        self.assertEqual(args.rfc, "Sat, 02 Jan 2010 07:41:11 GMT")

        args = self.format_arg(schema, {
            "datetime": "2010/01/02 01:11:11.12345678 +06:30",
            "rfc": "2010/01/02 01:11:11.12345678 +06:30",
        })
        self.assertEqual(args.datetime, "2010-01-01T18:41:11.123456Z")
        self.assertEqual(args.rfc, "Fri, 01 Jan 2010 18:41:11 GMT")

        args = self.format_arg(schema, {
            "datetime": "2010-01-02T00:00:00Z",
            "rfc": "2010-01-02T00:00:00Z",
        })
        self.assertEqual(args.datetime, "2010-01-02T00:00:00.000Z")
        self.assertEqual(args.rfc, "Sat, 02 Jan 2010 00:00:00 GMT")

        args = self.format_arg(schema, {
            "datetime": "2010-01-02 10:00:00 +00:00",
            "rfc": "2010-01-02 10:00:00 +00:00",
        })
        self.assertEqual(args.datetime, "2010-01-02T10:00:00.000Z")
        self.assertEqual(args.rfc, "Sat, 02 Jan 2010 10:00:00 GMT")

        args = self.format_arg(schema, {
            "datetime": None,
            "rfc": None,
        })
        self.assertEqual(args.datetime, None)
        self.assertEqual(args.rfc, None)

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            args = self.format_arg(schema, {
                "datetime": "-2010-01-a2 10:00:00 +00:00",
            })

    def test_uuid_fmt(self):
        from azure.cli.core.aaz import AAZUuidArg, AAZUuidFormat
        schema = AAZArgumentsSchema()
        schema.uuid = AAZUuidArg(
            nullable=True
        )

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": ""})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": "a8577a7a-4f31-40ab-bb00-3557df24a7e"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": "a8577a7a-4f31-40ab-bb003557df24a7ea"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": "a8577Z7Z-4f31-40ab-bb00-3557df24a7ea"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": "{a8577a7a-4f31-40ab-bb00-3557df24a7ea"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": "a8577a7a-4f31-40ab-bb00-3557df24a7ea}"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": "(a8577a7a-4f31-40ab-bb00-3557df24a7ea"})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"uuid": "a8577a7a-4f31-40ab-bb00-3557df24a7ea)"})

        args = self.format_arg(schema, {"uuid": "a8577a7a-4f31-40ab-bb00-3557df24a7ea"})
        self.assertEqual(args.uuid, "a8577a7a-4f31-40ab-bb00-3557df24a7ea")

        args = self.format_arg(schema, {"uuid": "FF0B2DF5-97EB-4E45-B028-8B0BEC803ABE"})
        self.assertEqual(args.uuid, "FF0B2DF5-97EB-4E45-B028-8B0BEC803ABE")

        args = self.format_arg(schema, {"uuid": "a8577A7a-4f31-40Ab-bb00-3557Df24a7Ea"})
        self.assertEqual(args.uuid, "a8577A7a-4f31-40Ab-bb00-3557Df24a7Ea")

        args = self.format_arg(schema, {"uuid": "{a8577a7a-4f31-40ab-bb00-3557df24a7ea}"})
        self.assertEqual(args.uuid, "a8577a7a-4f31-40ab-bb00-3557df24a7ea")

        args = self.format_arg(schema, {"uuid": "(a8577a7a-4f31-40ab-bb00-3557df24a7ea)"})
        self.assertEqual(args.uuid, "a8577a7a-4f31-40ab-bb00-3557df24a7ea")

        args = self.format_arg(schema, {"uuid": "a8577a7a4f3140abBb003557df24a7eA"})
        self.assertEqual(args.uuid, "a8577a7a-4f31-40ab-Bb00-3557df24a7eA")

        args = self.format_arg(schema, {"uuid": "{a8577a7a4f3140abbb003557df24a7ea}"})
        self.assertEqual(args.uuid, "a8577a7a-4f31-40ab-bb00-3557df24a7ea")

        args = self.format_arg(schema, {"uuid": "(a8577a7a4f3140abbb003557df24a7ea)"})
        self.assertEqual(args.uuid, "a8577a7a-4f31-40ab-bb00-3557df24a7ea")

        schema = AAZArgumentsSchema()
        schema.uuid = AAZUuidArg(
            fmt=AAZUuidFormat(case='upper'),
            nullable=True
        )

        args = self.format_arg(schema, {"uuid": "(a8577a7A4f3140Abbb003557df24a7ea)"})
        self.assertEqual(args.uuid, "A8577A7A-4F31-40AB-BB00-3557DF24A7EA")

        schema = AAZArgumentsSchema()
        schema.uuid = AAZUuidArg(
            fmt=AAZUuidFormat(case='lower'),
            nullable=True
        )

        args = self.format_arg(schema, {"uuid": "(A8577A7A4F3140Abbb003557DF24A7EA)"})
        self.assertEqual(args.uuid, "a8577a7a-4f31-40ab-bb00-3557df24a7ea")

        schema = AAZArgumentsSchema()
        schema.uuid = AAZUuidArg(
            fmt=AAZUuidFormat(hyphens_filled=False),
            nullable=True
        )

        args = self.format_arg(schema, {"uuid": "(A8577A7A4F3140Abbb003557DF24A7EA)"})
        self.assertEqual(args.uuid, "A8577A7A4F3140Abbb003557DF24A7EA")

        schema = AAZArgumentsSchema()
        schema.uuid = AAZUuidArg(
            fmt=AAZUuidFormat(braces_removed=False),
            nullable=True
        )

        args = self.format_arg(schema, {"uuid": "(a8577a7a4f3140abbb003557df24a7ea)"})
        self.assertEqual(args.uuid, "(a8577a7a-4f31-40ab-bb00-3557df24a7ea)")

        schema = AAZArgumentsSchema()
        schema.uuid = AAZUuidArg(
            fmt=AAZUuidFormat(braces_removed=False, hyphens_filled=False),
            nullable=True
        )

        args = self.format_arg(schema, {"uuid": "(A8577A7A4F3140Abbb003557DF24A7EA)"})
        self.assertEqual(args.uuid, "(A8577A7A4F3140Abbb003557DF24A7EA)")

        args = self.format_arg(schema, {"uuid": None})
        self.assertEqual(args.uuid, None)

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

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"int1": 10})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"int1": 25})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
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

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"flt1": 1.1})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"flt1": 22})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"flt1": 33})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"flt1": 23})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"flt1": 23.099})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"flt1": 31.901})

        args = self.format_arg(schema, {"flt1": 23.1})
        self.assertEqual(args.flt1, 23.1)

        args = self.format_arg(schema, {"flt1": 31.9})
        self.assertEqual(args.flt1, 31.9)

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {"flt1": 22.0000000001})

        with self.assertRaises(azclierror.InvalidArgumentValueError):
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

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "properties": {
                    "name": "abcd",
                }
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
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

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "properties": {
                    "name": "a1234",
                }
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "properties": {
                    "count": -10,
                }
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
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

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "tags": {
                    "flag1": "v1",
                },
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "tags": {
                    "flag1": "v1",
                    "flag2": "v2",
                    "flag3": "v3",
                    "flag4": "v4",
                },
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
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

    def test_freeform_dict_fmt(self):
        from azure.cli.core.aaz import AAZFreeFormDictArgFormat
        from azure.cli.core.aaz import AAZFreeFormDictArg

        schema = AAZArgumentsSchema()
        schema.tags = AAZFreeFormDictArg(fmt=AAZFreeFormDictArgFormat(max_properties=3, min_properties=2), nullable=True)

        args = self.format_arg(schema, {
            "tags": {
                "flag1": "v1",
                "flag2": 2,
            },
        })
        self.assertEqual(args.to_serialized_data(), {
            "tags": {
                "flag1": "v1",
                "flag2": 2,
            }
        })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "tags": {
                    "flag1": "v1",
                },
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "tags": {
                    "flag1": "v1",
                    "flag2": "v2",
                    "flag3": "v3",
                    "flag4": "v4",
                },
            })

        args = self.format_arg(schema, {
            "tags": None,
        })
        self.assertEqual(args.to_serialized_data(), {
            "tags": None
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

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "tags": ['v1',],
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "tags": ['v1', 'v2', 'v3', 'v4'],
            })

        with self.assertRaises(azclierror.InvalidArgumentValueError):
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

    def test_aaz_file_arg_fmt(self):
        from azure.cli.core.aaz import AAZArgumentsSchema, AAZFileArg, AAZFileArgTextFormat, \
            AAZFileArgBase64EncodeFormat
        import os
        import random
        schema = AAZArgumentsSchema()
        v = schema()

        schema.text = AAZFileArg(fmt=AAZFileArgTextFormat())
        test_file = "test_aaz_file_arg_fmt.txt"
        content = "This is test"
        with open(test_file, 'w') as f:
            f.write(content)

        args = self.format_arg(schema, {
            "text": test_file,
        })

        self.assertEqual(args.to_serialized_data(), {
            "text": content
        })

        os.remove(test_file)
        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "text": test_file,
            })

        schema.data = AAZFileArg(fmt=AAZFileArgBase64EncodeFormat())
        data_file = "test_aaz_file_arg_fmt.data"
        data = bytes([random.randrange(0, 256) for _ in range(0, 128)])
        with open(data_file, 'wb') as f:
            f.write(data)

        args = self.format_arg(schema, {
            "data": data_file,
        })
        self.assertEqual(args.to_serialized_data(), {
            "data": base64.b64encode(data).decode("utf-8")
        })

        os.remove(data_file)
        with self.assertRaises(azclierror.InvalidArgumentValueError):
            self.format_arg(schema, {
                "data": data_file,
            })
