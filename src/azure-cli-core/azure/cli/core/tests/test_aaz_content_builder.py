# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestAAZContentBuilder(unittest.TestCase):

    @staticmethod
    def _define_args_schema():
        from azure.cli.core.aaz._arg import AAZArgumentsSchema, AAZStrArg, AAZObjectArg, AAZListArg, AAZDictArg
        _schema = AAZArgumentsSchema()

        # str
        _schema.name = AAZStrArg(nullable=True)

        # object
        _schema.obj = AAZObjectArg(nullable=True)
        _schema.obj.prop1 = AAZStrArg()

        _schema.h_obj = AAZObjectArg(nullable=True)
        _schema.h_obj.prop1 = AAZStrArg()

        # dict<str, str>
        _schema.tags = AAZDictArg(nullable=True)
        _schema.tags.Element = AAZStrArg()

        # dict<str, str>
        _schema.h_tags = AAZDictArg(nullable=True)
        _schema.h_tags.Element = AAZStrArg()

        # list<str>
        _schema.permissions = AAZListArg(nullable=True)
        _schema.permissions.Element = AAZStrArg()

        _schema.h_permissions = AAZListArg(nullable=True)
        _schema.h_permissions.Element = AAZStrArg()

        # list<object>
        _schema.subnets = AAZListArg()
        _schema.subnets.Element = AAZObjectArg(nullable=True)
        _schema.subnets.Element.name = AAZStrArg()

        # list<list<str>>
        _schema.adds = AAZListArg()
        _schema.adds.Element = AAZListArg(nullable=True)
        _schema.adds.Element.Element = AAZStrArg()

        # dict<str, object>
        _schema.domains = AAZDictArg()
        _schema.domains.Element = AAZObjectArg(nullable=True)
        _schema.domains.Element.name = AAZStrArg()

        # dict<str, dict<str, str>>
        _schema.conns = AAZDictArg()
        _schema.conns.Element = AAZDictArg(nullable=True)
        _schema.conns.Element.Element = AAZStrArg()

        _schema.actions = AAZListArg()
        element = _schema.actions.Element = AAZObjectArg()
        element.name = AAZStrArg()

        element.action_a = AAZObjectArg()
        element.action_a.web = AAZStrArg()
        element.action_a.author = AAZStrArg()

        element.action_b = AAZObjectArg()
        element.action_b.machine = AAZStrArg()
        element.action_b.country = AAZStrArg()

        element.action_c = AAZStrArg()
        element.action_d = AAZStrArg()

        return _schema

    def test_aaz_content_builder_for_create(self):
        from azure.cli.core.aaz._content_builder import AAZContentBuilder
        from azure.cli.core.aaz._arg_browser import AAZArgBrowser
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType

        _args_schema = self._define_args_schema()
        arg_value = _args_schema(data={
            "name": "a",
            "obj": {
                "prop1": "pp1",
            },
            "tags": {
                "tag_a": "a",
                "tag_b": "b",
            },
            "permissions": [
                "read", "write",
            ],
            "subnets": [
                {
                    "name": "net1",
                },
                {
                    "name": "net2",
                }
            ],
            "adds": [
                ["0"],
                ["0", "1", "2"],
                ["2", "3"],
            ],
            "domains": {
                "a": {
                    "name": "0",
                },
                "b": {
                    "name": "1",
                },
                "c": {
                    "name": "2",
                }
            },
            "conns": {
                "a": {
                    "a1": "0",
                    "a2": "1",
                },
                "b": {
                    "b1": "3",
                    "b2": "6",
                }
            }
        })
        arg_data = arg_value.to_serialized_data()
        schema = AAZObjectType()
        _value = AAZObjectType._ValueCls(
            schema=schema,
            data=schema.process_data(None)
        )

        _builder = AAZContentBuilder(
            values=[_value],
            args=[AAZArgBrowser(arg_value=arg_value, arg_data=arg_data)]
        )

        _builder.set_prop('name', AAZStrType, '.name')

        self.assertTrue(
            _value.to_serialized_data()['name'] == 'a'
        )

        _builder.set_prop('obj', AAZObjectType, '.obj')
        _builder.set_prop('hideObj', AAZObjectType, '.h_obj')

        obj = _builder.get('.obj')
        if obj is not None:
            obj.set_prop('prop1', AAZStrType, '.prop1')

        hide_obj = _builder.get('.hideObj')
        if hide_obj:
            hide_obj.set_prop('prop1', AAZStrType, '.prop1')

        self.assertEqual(
            _value.to_serialized_data()['obj'], {'prop1': "pp1"}
        )
        self.assertTrue('hideObj' not in _value.to_serialized_data())

        _builder.set_prop('tags', AAZDictType, '.tags')
        _builder.set_prop('hideTags', AAZDictType, '.h_tags')

        tags = _builder.get('.tags')
        if tags is not None:
            tags.set_elements(AAZStrType, '.')

        hide_tags = _builder.get('.hideTags')
        if hide_tags:
            hide_tags.set_elements(AAZStrType, '.')

        self.assertEqual(_value.to_serialized_data()['tags'], {'tag_a': 'a', 'tag_b': 'b'})
        self.assertTrue('hideTags' not in _value.to_serialized_data())

        _builder.set_prop('permissions', AAZListType, '.permissions')
        _builder.set_prop('hidePermissions', AAZListType, '.h_permissions')

        permissions = _builder.get('.permissions')
        if permissions:
            permissions.set_elements(AAZStrType, '.')

        hide_permissions = _builder.get('.hidePermissions')
        if hide_permissions:
            hide_permissions.set_elements(AAZStrType, '.')

        self.assertTrue(_value.to_serialized_data()['permissions'] == ['read', 'write'])
        self.assertTrue('hidePermissions' not in _value.to_serialized_data())

        _builder.set_prop('properties', AAZObjectType)

        self.assertTrue('properties' not in _value.to_serialized_data())

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('subnets', AAZListType, '.subnets')

        subnets = _builder.get('.properties.subnets')
        if subnets:
            subnets.set_elements(AAZObjectType, '.')

        elements = _builder.get('.properties.subnets[]')
        if elements:
            elements.set_prop('name', AAZStrType, '.name')

        self.assertEqual(_value.to_serialized_data()['properties']['subnets'], [
            {'name': 'net1'},
            {'name': 'net2'}
        ])

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('adds', AAZListType, '.adds')

        adds = _builder.get('.properties.adds')
        if adds:
            adds.set_elements(AAZListType, '.')

        elements = _builder.get('.properties.adds[]')
        if elements:
            elements.set_elements(AAZObjectType)

        elements = _builder.get('.properties.adds[][]')
        if elements:
            elements.set_prop('name', AAZStrType, '.')

        self.assertEqual(_value.to_serialized_data()['properties']['adds'], [
            [{'name': '0'}],
            [{'name': '0'}, {'name': '1'}, {'name': '2'}],
            [{'name': '2'}, {'name': '3'}]
        ])

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('domains', AAZDictType, '.domains')

        domains = _builder.get('.properties.domains')
        if domains:
            domains.set_elements(AAZObjectType, '.')

        elements = _builder.get('.properties.domains{}')
        if elements:
            elements.set_prop('name', AAZStrType, '.name')

        self.assertEqual(_value.to_serialized_data()['properties']['domains'], {
            'a': {'name': '0'},
            'b': {'name': '1'},
            'c': {'name': '2'}
        })

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('conns', AAZDictType, '.conns')

        conns = _builder.get('.properties.conns')
        if conns:
            conns.set_elements(AAZDictType, '.')

        elements = _builder.get('.properties.conns{}')
        if elements:
            elements.set_elements(AAZObjectType)

        elements = _builder.get('.properties.conns{}{}')
        if elements:
            elements.set_prop('name', AAZStrType, '.')

        self.assertTrue(_value.to_serialized_data()['properties']['conns'] == {
            'a': {
                'a1': {'name': '0'},
                'a2': {'name': '1'}
            },
            'b': {
                'b1': {'name': '3'},
                'b2': {'name': '6'},
            }
        })

        self.assertEqual(_value.to_serialized_data(),
                         {'name': 'a',
                          'obj': {'prop1': 'pp1'},
                          'tags': {'tag_a': 'a', 'tag_b': 'b'},
                          'permissions': ['read', 'write'],
                          'properties': {'subnets': [{'name': 'net1'}, {'name': 'net2'}],
                                         'adds': [[{'name': '0'}],
                                                  [{'name': '0'}, {'name': '1'},
                                                   {'name': '2'}],
                                                  [{'name': '2'}, {'name': '3'}]],
                                         'domains': {'a': {'name': '0'},
                                                     'b': {'name': '1'},
                                                     'c': {'name': '2'}}, 'conns': {
                                  'a': {'a1': {'name': '0'}, 'a2': {'name': '1'}},
                                  'b': {'b1': {'name': '3'}, 'b2': {'name': '6'}}}}})

    def _define_instance_value(self):
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType
        from azure.cli.core.aaz._field_value import AAZObject

        _schema = AAZObjectType()

        _schema.name = AAZStrType()
        _schema.obj = AAZObjectType()
        _schema.obj.prop1 = AAZStrType()
        _schema.hideObj = AAZObjectType(nullable=True)
        _schema.hideObj.prop1 = AAZStrType()

        _schema.tags = AAZDictType()
        _schema.tags.Element = AAZStrType()
        _schema.hideTags = AAZDictType(nullable=True)
        _schema.hideTags.Element = AAZStrType()
        _schema.permissions = AAZListType()
        _schema.permissions.Element = AAZStrType()
        _schema.hidePermissions = AAZListType(nullable=True)
        _schema.hidePermissions.Element = AAZStrType()
        _schema.properties = AAZObjectType()
        _schema.properties.subnets = AAZListType()
        _schema.properties.subnets.Element = AAZObjectType(nullable=True)
        _schema.properties.subnets.Element.name = AAZStrType()
        _schema.properties.adds = AAZListType()
        _schema.properties.adds.Element = AAZListType()
        _schema.properties.adds.Element.Element = AAZObjectType()
        _schema.properties.adds.Element.Element.name = AAZStrType()
        _schema.properties.domains = AAZDictType()
        _schema.properties.domains.Element = AAZObjectType(nullable=True)
        _schema.properties.domains.Element.name = AAZStrType()
        _schema.properties.conns = AAZDictType()
        _schema.properties.conns.Element = AAZDictType()
        _schema.properties.conns.Element.Element = AAZObjectType()
        _schema.properties.conns.Element.Element.name = AAZStrType()

        value = AAZObject(_schema, data=_schema.process_data({
            'name': 'a',
            'obj': {'prop1': 'pp1'},
            'hideObj': {'prop1': 'hp1'},
            'tags': {'tag_a': 'a', 'tag_b': 'b'},
            'hideTags': {'h_tag_a': 'a', 'h_tag_b': 'b'},
            'permissions': ['read', 'write'],
            'hidePermissions': ['read', 'write'],
            'properties': {
                'subnets': [{'name': 'net1'}, {'name': 'net2'}],
                'adds': [[{'name': '0'}], [{'name': '0'}, {'name': '1'}, {'name': '2'}],
                         [{'name': '2'}, {'name': '3'}]],
                'domains': {'a': {'name': '0'}, 'b': {'name': '1'}, 'c': {'name': '2'}},
                'conns': {'a': {'a1': {'name': '0'}, 'a2': {'name': '1'}}, 'b': {'b1': {'name': '3'}}}
            }
        }))

        return value

    def test_aaz_content_builder_for_update(self):
        from azure.cli.core.aaz._content_builder import AAZContentBuilder
        from azure.cli.core.aaz._arg_browser import AAZArgBrowser
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType

        _value = self._define_instance_value()

        _args_schema = self._define_args_schema()
        arg_value = _args_schema(data={})
        arg_value.name = 'b'

        arg_value.obj.prop1 = 'p2'
        arg_value.h_obj.prop1 = 'hh'

        arg_value.tags = {
            'tag_a': '2'
        }

        arg_value.h_tags['h_tag_a'] = '2'

        arg_value.permissions = ["write"]

        arg_value.h_permissions[0] = 'copy'
        arg_value.h_permissions[2] = 'delete'

        arg_value.subnets[0].name = 'net'
        arg_value.subnets[2] = {'name': "net3"}

        arg_value.adds[0][1] = '1'
        arg_value.adds[1] = ['1', '2']
        arg_value.adds[3][0] = '4'

        arg_value.domains['a'].name = 'a'
        arg_value.domains['d'] = {'name': 'd'}

        arg_value.conns['a'] = {'f1': 'f1'}
        arg_value.conns['b']['b1'] = 'b1'
        arg_value.conns['b']['b3'] = "b3"
        arg_value.conns['d'] = {"d": "d"}

        _builder = AAZContentBuilder(
            values=[_value],
            args=[AAZArgBrowser(arg_value=arg_value, arg_data=arg_value.to_serialized_data())]
        )

        _builder.set_prop('name', AAZStrType, '.name')

        self.assertTrue(_value.to_serialized_data()['name'] == 'b')

        _builder.set_prop('obj', AAZObjectType, '.obj')
        _builder.set_prop('hideObj', AAZObjectType, '.h_obj')

        obj = _builder.get('.obj')
        if obj is not None:
            obj.set_prop('prop1', AAZStrType, '.prop1')

        hide_obj = _builder.get('.hideObj')
        if hide_obj:
            hide_obj.set_prop('prop1', AAZStrType, '.prop1')

        self.assertEqual(
            _value.to_serialized_data()['obj'], {'prop1': "p2"}
        )
        self.assertEqual(
            _value.to_serialized_data()['hideObj'], {'prop1': "hh"}
        )

        _builder.set_prop('tags', AAZDictType, '.tags')
        _builder.set_prop('hideTags', AAZDictType, '.h_tags')

        tags = _builder.get('.tags')
        if tags is not None:
            tags.set_elements(AAZStrType, '.')

        hide_tags = _builder.get('.hideTags')
        if hide_tags:
            hide_tags.set_elements(AAZStrType, '.')

        self.assertTrue(_value.to_serialized_data()['tags'] == {'tag_a': '2'})
        self.assertTrue(_value.to_serialized_data()['hideTags'] == {'h_tag_a': '2', 'h_tag_b': 'b'})

        _builder.set_prop('permissions', AAZListType, '.permissions')
        _builder.set_prop('hidePermissions', AAZListType, '.h_permissions')

        permissions = _builder.get('.permissions')
        if permissions:
            permissions.set_elements(AAZStrType, '.')

        hide_permissions = _builder.get('.hidePermissions')
        if hide_permissions:
            hide_permissions.set_elements(AAZStrType, '.')

        self.assertTrue(_value.to_serialized_data()['permissions'] == ['write'])
        self.assertTrue(_value.to_serialized_data()['hidePermissions'] == ['copy', 'write', 'delete'])

        _builder.set_prop('properties', AAZObjectType)

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('subnets', AAZListType, '.subnets')

        subnets = _builder.get('.properties.subnets')
        if subnets:
            subnets.set_elements(AAZObjectType, '.')

        elements = _builder.get('.properties.subnets[]')
        if elements:
            elements.set_prop('name', AAZStrType, '.name')

        self.assertEqual(_value.to_serialized_data()['properties']['subnets'], [
            {'name': 'net'},
            {'name': 'net2'},
            {'name': 'net3'},
        ])

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('adds', AAZListType, '.adds')

        adds = _builder.get('.properties.adds')
        if adds:
            adds.set_elements(AAZListType, '.')

        elements = _builder.get('.properties.adds[]')
        if elements:
            elements.set_elements(AAZObjectType)

        elements = _builder.get('.properties.adds[][]')
        if elements:
            elements.set_prop('name', AAZStrType, '.')

        self.assertEqual(_value.to_serialized_data()['properties']['adds'], [
            [{'name': '0'}, {'name': '1'}],
            [{'name': '1'}, {'name': '2'}],
            [{'name': '2'}, {'name': '3'}],
            [{'name': '4'}]
        ])

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('domains', AAZDictType, '.domains')

        domains = _builder.get('.properties.domains')
        if domains:
            domains.set_elements(AAZObjectType, '.')

        elements = _builder.get('.properties.domains{}')
        if elements:
            elements.set_prop('name', AAZStrType, '.name')

        self.assertEqual(_value.to_serialized_data()['properties']['domains'], {
            'a': {'name': 'a'},
            'b': {'name': '1'},
            'c': {'name': '2'},
            'd': {'name': 'd'},
        })

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('conns', AAZDictType, '.conns')

        conns = _builder.get('.properties.conns')
        if conns:
            conns.set_elements(AAZDictType, '.')

        elements = _builder.get('.properties.conns{}')
        if elements:
            elements.set_elements(AAZObjectType)

        elements = _builder.get('.properties.conns{}{}')
        if elements:
            elements.set_prop('name', AAZStrType, '.')

        self.assertEqual(_value.to_serialized_data()['properties']['conns'], {
            'a': {
                'f1': {'name': 'f1'},
            },
            'b': {
                'b1': {'name': 'b1'},
                'b3': {'name': 'b3'},
            },
            'd': {
                'd': {'name': 'd'}
            }
        })

        self.assertEqual(_value.to_serialized_data(), {
            'name': 'b',
            'obj': {'prop1': 'p2'},
            'hideObj': {'prop1': 'hh'},
            'tags': {'tag_a': '2'},
            'hideTags': {'h_tag_a': '2', 'h_tag_b': 'b'},
            'permissions': ['write'],
            'hidePermissions': ['copy', 'write', 'delete'],
            'properties': {
                'subnets': [{'name': 'net'}, {'name': 'net2'}, {'name': 'net3'}],
                'adds': [[{'name': '0'}, {'name': '1'}], [{'name': '1'}, {'name': '2'}], [{'name': '2'}, {'name': '3'}],
                         [{'name': '4'}]],
                'domains': {'a': {'name': 'a'}, 'b': {'name': '1'}, 'c': {'name': '2'}, 'd': {'name': 'd'}},
                'conns': {'a': {'f1': {'name': 'f1'}}, 'b': {'b1': {'name': 'b1'}, 'b3': {'name': 'b3'}},
                          'd': {'d': {'name': 'd'}}}
            }
        })

    def test_aaz_content_builder_for_update_with_nullable(self):
        from azure.cli.core.aaz._content_builder import AAZContentBuilder
        from azure.cli.core.aaz._arg_browser import AAZArgBrowser
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType, AAZUndefined
        from azure.cli.core.aaz._operation import AAZHttpOperation

        _value = self._define_instance_value()

        _args_schema = self._define_args_schema()
        arg_value = _args_schema(data={})

        arg_value.name = None
        arg_value.obj = None
        arg_value.h_obj = None
        arg_value.tags = None
        arg_value.h_tags = None
        arg_value.permissions = None
        arg_value.h_permissions = None

        arg_value.subnets[0] = None
        arg_value.domains['a'] = None

        arg_value.adds[0] = None
        arg_value.adds[4] = None

        arg_value.conns['a'] = None
        arg_value.conns['d'] = None

        _builder = AAZContentBuilder(
            values=[_value],
            args=[AAZArgBrowser(arg_value=arg_value, arg_data=arg_value.to_serialized_data())]
        )

        _builder.set_prop('name', AAZStrType, '.name')
        self.assertTrue('name' not in _value.to_serialized_data())

        _builder.set_prop('obj', AAZObjectType, '.obj')
        _builder.set_prop('hideObj', AAZObjectType, '.h_obj')

        obj = _builder.get('.obj')
        if obj is not None:
            obj.set_prop('prop1', AAZStrType, '.prop1')

        hide_obj = _builder.get('.hideObj')
        if hide_obj:
            hide_obj.set_prop('prop1', AAZStrType, '.prop1')

        self.assertTrue('obj' not in _value.to_serialized_data())
        self.assertTrue(_value.to_serialized_data()['hideObj'] is None)

        _builder.set_prop('tags', AAZDictType, '.tags')
        _builder.set_prop('hideTags', AAZDictType, '.h_tags')

        tags = _builder.get('.tags')
        if tags is not None:
            tags.set_elements(AAZStrType, '.')

        hide_tags = _builder.get('.hideTags')
        if hide_tags:
            hide_tags.set_elements(AAZStrType, '.')

        self.assertTrue('tags' not in _value.to_serialized_data())
        self.assertTrue(_value.to_serialized_data()['hideTags'] is None)

        _builder.set_prop('permissions', AAZListType, '.permissions')
        _builder.set_prop('hidePermissions', AAZListType, '.h_permissions')

        permissions = _builder.get('.permissions')
        if permissions:
            permissions.set_elements(AAZStrType, '.')

        hide_permissions = _builder.get('.hidePermissions')
        if hide_permissions:
            hide_permissions.set_elements(AAZStrType, '.')

        self.assertTrue('permissions' not in _value.to_serialized_data())
        self.assertTrue(_value.to_serialized_data()['hidePermissions'] is None)

        _builder.set_prop('properties', AAZObjectType)

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('subnets', AAZListType, '.subnets')

        subnets = _builder.get('.properties.subnets')
        if subnets:
            subnets.set_elements(AAZObjectType, '.')

        elements = _builder.get('.properties.subnets[]')
        if elements:
            elements.set_prop('name', AAZStrType, '.name')

        self.assertEqual(_value.to_serialized_data()['properties']['subnets'], [
            None,
            {'name': 'net2'},
        ])

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('domains', AAZDictType, '.domains')

        domains = _builder.get('.properties.domains')
        if domains:
            domains.set_elements(AAZObjectType, '.')

        elements = _builder.get('.properties.domains{}')
        if elements:
            elements.set_prop('name', AAZStrType, '.name')

        self.assertEqual(_value.to_serialized_data()['properties']['domains'], {
            'a': None,
            'b': {'name': '1'},
            'c': {'name': '2'}
        })

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('adds', AAZListType, '.adds')

        adds = _builder.get('.properties.adds')
        if adds:
            adds.set_elements(AAZListType, '.')

        elements = _builder.get('.properties.adds[]')
        if elements:
            elements.set_elements(AAZObjectType)

        elements = _builder.get('.properties.adds[][]')
        if elements:
            elements.set_prop('name', AAZStrType, '.')

        self.assertEqual(_value.to_serialized_data()['properties']['adds'], [
            AAZUndefined,
            [{'name': '0'}, {'name': '1'}, {'name': '2'}],
            [{'name': '2'}, {'name': '3'}],
            AAZUndefined,
            AAZUndefined,
        ])

        self.assertEqual(AAZHttpOperation.serialize_content(_value)['properties']['adds'], [
            [{'name': '0'}, {'name': '1'}, {'name': '2'}],
            [{'name': '2'}, {'name': '3'}],
        ])

        properties = _builder.get('.properties')
        if properties:
            properties.set_prop('conns', AAZDictType, '.conns')

        conns = _builder.get('.properties.conns')
        if conns:
            conns.set_elements(AAZDictType, '.')

        elements = _builder.get('.properties.conns{}')
        if elements:
            elements.set_elements(AAZObjectType)

        elements = _builder.get('.properties.conns{}{}')
        if elements:
            elements.set_prop('name', AAZStrType, '.')

        self.assertEqual(_value.to_serialized_data()['properties']['conns'], {
            'b': {'b1': {'name': '3'}}
        })

        self.assertEqual(AAZHttpOperation.serialize_content(_value), {
            'hideObj': None, 'hideTags': None, 'hidePermissions': None,
            'properties': {
                'subnets': [None, {'name': 'net2'}],
                'adds': [[{'name': '0'}, {'name': '1'}, {'name': '2'}], [{'name': '2'}, {'name': '3'}]],
                'domains': {'a': None, 'b': {'name': '1'}, 'c': {'name': '2'}}, 'conns': {'b': {'b1': {'name': '3'}}}}
        })

    def test_aaz_content_builder_for_polymorphism(self):
        from azure.cli.core.aaz._content_builder import AAZContentBuilder
        from azure.cli.core.aaz._arg_browser import AAZArgBrowser
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType

        _args_schema = self._define_args_schema()
        arg_value = _args_schema(data={
            "name": "a",
            "actions": [
                {
                    "name": "A 1",
                    "action_a": {
                        "web": "Web 1",
                        "author": "Author 1"
                    }
                },
                {
                    "name": "B 1",
                    "action_b": {
                        "machine": "Machine 1",
                        "country": "Country 1",
                    }
                },
                {
                    "name": "A 2",
                    "action_a": {
                        "web": "Web 2",
                        "author": "Author 2"
                    }
                },
                {
                    "name": "B 2",
                    "action_b": {
                        "machine": "Machine 2",
                        "country": "Country 2",
                    }
                },
                {
                    "name": "C 1",
                    "action_c": "Str C"
                }
            ]
        })
        arg_data = arg_value.to_serialized_data()
        schema = AAZObjectType()
        _value = AAZObjectType._ValueCls(
            schema=schema,
            data=schema.process_data(None)
        )

        _builder = AAZContentBuilder(
            values=[_value],
            args=[AAZArgBrowser(arg_value=arg_value, arg_data=arg_data)]
        )

        _builder.set_prop("name", AAZStrType, '.name')
        self.assertTrue(
            _value.to_serialized_data()['name'] == 'a'
        )

        _builder.set_prop('actions', AAZListType, '.actions')

        actions = _builder.get('.actions')
        if actions:
            actions.set_elements(AAZObjectType, '.')

        elements = _builder.get('.actions[]')
        if elements:
            elements.set_prop('name', AAZStrType, '.name')
            elements.set_const('type', 'A', AAZStrType, '.action_a')
            elements.set_const('type', 'B', AAZStrType, '.action_b')
            elements.set_const('type', 'C', AAZStrType, '.action_c')
            elements.set_const('type', 'D', AAZStrType, '.action_d')
            elements.set_const('default', 'Default', AAZStrType)

            elements.discriminate_by('type', 'A')
            elements.discriminate_by('type', 'B')
            elements.discriminate_by('type', 'C')
            elements.discriminate_by('type', 'D')

        self.assertTrue(_value.to_serialized_data()['actions'] == [
            {'name': 'A 1', 'type': 'A', 'default': 'Default'},
            {'name': 'B 1', 'type': 'B', 'default': 'Default'},
            {'name': 'A 2', 'type': 'A', 'default': 'Default'},
            {'name': 'B 2', 'type': 'B', 'default': 'Default'},
            {'name': 'C 1', 'type': 'C', 'default': 'Default'},
        ])

        disc_a = _builder.get('.actions[]{type:A}')
        if disc_a:
            disc_a.set_prop("web", AAZStrType, '.action_a.web')
            disc_a.set_prop("author", AAZStrType, '.action_a.author')

        disc_b = _builder.get('.actions[]{type:B}')
        if disc_b:
            disc_b.set_prop("machine", AAZStrType, '.action_b.machine')
            disc_b.set_prop("country", AAZStrType, '.action_b.country')

        disc_c = _builder.get('.actions[]{type:C}')
        if disc_c:
            disc_c.set_prop("kind", AAZStrType, '.action_c')

        disc_d = _builder.get('.actions[]{type:D}')
        if disc_d:
            disc_d.set_prop("people", AAZStrType, '.action_d')

        self.assertTrue(_value.to_serialized_data()['actions'] == [
            {'name': 'A 1', 'type': 'A', 'default': 'Default', 'web': 'Web 1', 'author': 'Author 1'},
            {'name': 'B 1', 'type': 'B', 'default': 'Default', 'machine': 'Machine 1', 'country': 'Country 1'},
            {'name': 'A 2', 'type': 'A', 'default': 'Default', 'web': 'Web 2', 'author': 'Author 2'},
            {'name': 'B 2', 'type': 'B', 'default': 'Default', 'machine': 'Machine 2', 'country': 'Country 2'},
            {'name': 'C 1', 'type': 'C', 'default': 'Default', 'kind': 'Str C'}
        ])

        self.assertTrue(_value.actions[0].web == "Web 1")
        element_schema = _value.actions._schema.Element

        self.assertTrue(element_schema.get_attr_name("name") is not None)
        self.assertTrue(element_schema.get_attr_name("type") is not None)

        self.assertTrue(element_schema._discriminator_field_name == "type")

        self.assertTrue(element_schema._discriminators['A'].get_attr_name('web') is not None)
        self.assertTrue(element_schema._discriminators['A'].get_attr_name('author') is not None)
        self.assertTrue(element_schema._discriminators['A'].get_attr_name('machine') is None)
        self.assertTrue(element_schema._discriminators['A'].get_attr_name('country') is None)
        self.assertTrue(element_schema._discriminators['A'].get_attr_name('kind') is None)
        self.assertTrue(element_schema._discriminators['A'].get_attr_name('people') is None)

        self.assertTrue(element_schema._discriminators['B'].get_attr_name('web') is None)
        self.assertTrue(element_schema._discriminators['B'].get_attr_name('author') is None)
        self.assertTrue(element_schema._discriminators['B'].get_attr_name('machine') is not None)
        self.assertTrue(element_schema._discriminators['B'].get_attr_name('country') is not None)
        self.assertTrue(element_schema._discriminators['B'].get_attr_name('kind') is None)
        self.assertTrue(element_schema._discriminators['B'].get_attr_name('people') is None)

        self.assertTrue(element_schema._discriminators['C'].get_attr_name('web') is None)
        self.assertTrue(element_schema._discriminators['C'].get_attr_name('author') is None)
        self.assertTrue(element_schema._discriminators['C'].get_attr_name('machine') is None)
        self.assertTrue(element_schema._discriminators['C'].get_attr_name('country') is None)
        self.assertTrue(element_schema._discriminators['C'].get_attr_name('kind') is not None)
        self.assertTrue(element_schema._discriminators['C'].get_attr_name('people') is None)

        self.assertTrue(element_schema._discriminators['D'].get_attr_name('web') is None)
        self.assertTrue(element_schema._discriminators['D'].get_attr_name('author') is None)
        self.assertTrue(element_schema._discriminators['D'].get_attr_name('machine') is None)
        self.assertTrue(element_schema._discriminators['D'].get_attr_name('country') is None)
        self.assertTrue(element_schema._discriminators['D'].get_attr_name('kind') is None)
        self.assertTrue(element_schema._discriminators['D'].get_attr_name('people') is None)
