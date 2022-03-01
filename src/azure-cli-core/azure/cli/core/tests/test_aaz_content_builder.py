import unittest
import json
from azure.cli.core import azclierror
from azure.cli.core.aaz import exceptions as aazerror


class TestAAZContentBuilder(unittest.TestCase):

    @staticmethod
    def _define_args_schema():
        from azure.cli.core.aaz._arg import AAZArgumentsSchema, AAZStrArg, AAZObjectArg, AAZListArg, AAZDictArg
        _schema = AAZArgumentsSchema()

        # str
        _schema.name = AAZStrArg()

        # dict<str, str>
        _schema.tags = AAZDictArg()
        _schema.tags.Element = AAZStrArg()

        # dict<str, str>
        _schema.h_tags = AAZDictArg()
        _schema.h_tags.Element = AAZStrArg()

        # list<str>
        _schema.permissions = AAZListArg()
        _schema.permissions.Element = AAZStrArg()

        _schema.h_permissions = AAZListArg()
        _schema.h_permissions.Element = AAZStrArg()

        # list<object>
        _schema.subnets = AAZListArg()
        _schema.subnets.Element = AAZObjectArg()
        _schema.subnets.Element.name = AAZStrArg()

        # list<list<str>>
        _schema.adds = AAZListArg()
        _schema.adds.Element = AAZListArg()
        _schema.adds.Element.Element = AAZStrArg()

        # dict<str, object>
        _schema.domains = AAZDictArg()
        _schema.domains.Element = AAZObjectArg()
        _schema.domains.Element.name = AAZStrArg()

        # dict<str, dict<str, str>>
        _schema.conns = AAZDictArg()
        _schema.conns.Element = AAZDictArg()
        _schema.conns.Element.Element = AAZStrArg()
        return _schema

    def test_aaz_content_builder_for_create(self):
        from azure.cli.core.aaz._content_builder import AAZContentBuilder, AAZContentArgBrowser
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType

        _args_schema = self._define_args_schema()
        arg_value = _args_schema(data={
            "name": "a",
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
            args=[AAZContentArgBrowser(arg_value=arg_value, arg_data=arg_data)]
        )

        _builder.set_prop('name', AAZStrType, '.name')

        self.assertTrue(
            _value.to_serialized_data()['name'] == 'a'
        )

        _builder.set_prop('tags', AAZDictType, '.tags')
        _builder.set_prop('hideTags', AAZDictType, '.h_tags')

        tags = _builder.get('.tags')
        if tags is not None:
            tags.set_elements(AAZStrType, '.')

        hide_tags = _builder.get('.hideTags')
        if hide_tags:
            hide_tags.set_elements(AAZStrType, '.')

        self.assertTrue(_value.to_serialized_data()['tags'] == {'tag_a': 'a', 'tag_b': 'b'})
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

        self.assertTrue(_value.to_serialized_data()['properties']['subnets'] == [
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

        self.assertTrue(_value.to_serialized_data()['properties']['adds'] == [
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

        self.assertTrue(_value.to_serialized_data()['properties']['domains'] == {
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
                'b1': {'name': '3'}
            }
        })

        self.assertTrue(_value.to_serialized_data() == {'name': 'a', 'tags': {'tag_a': 'a', 'tag_b': 'b'}, 'permissions': ['read', 'write'], 'properties': {'subnets': [{'name': 'net1'}, {'name': 'net2'}], 'adds': [[{'name': '0'}], [{'name': '0'}, {'name': '1'}, {'name': '2'}], [{'name': '2'}, {'name': '3'}]], 'domains': {'a': {'name': '0'}, 'b': {'name': '1'}, 'c': {'name': '2'}}, 'conns': {'a': {'a1': {'name': '0'}, 'a2': {'name': '1'}}, 'b': {'b1': {'name': '3'}}}}})

    def _define_instance_value(self):
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType
        from azure.cli.core.aaz._field_value import AAZObject

        _schema = AAZObjectType()

        _schema.name = AAZStrType()
        _schema.tags = AAZDictType()
        _schema.tags.Element = AAZStrType()
        _schema.hideTags = AAZDictType()
        _schema.hideTags.Element = AAZStrType()
        _schema.permissions = AAZListType()
        _schema.permissions.Element = AAZStrType()
        _schema.hidePermissions = AAZListType()
        _schema.hidePermissions.Element = AAZStrType()
        _schema.properties = AAZObjectType()
        _schema.properties.subnets = AAZListType()
        _schema.properties.subnets.Element = AAZObjectType()
        _schema.properties.subnets.Element.name = AAZStrType()
        _schema.properties.adds = AAZListType()
        _schema.properties.adds.Element = AAZListType()
        _schema.properties.adds.Element.Element = AAZObjectType()
        _schema.properties.adds.Element.Element.name = AAZStrType()
        _schema.properties.domains = AAZDictType()
        _schema.properties.domains.Element = AAZObjectType()
        _schema.properties.domains.Element.name = AAZStrType()
        _schema.properties.conns = AAZDictType()
        _schema.properties.conns.Element = AAZDictType()
        _schema.properties.conns.Element.Element = AAZObjectType()
        _schema.properties.conns.Element.Element.name = AAZStrType()

        value = AAZObject(_schema, data=_schema.process_data({
            'name': 'a',
            'tags': {'tag_a': 'a', 'tag_b': 'b'},
            'hideTags': {'h_tag_a': 'a', 'h_tag_b': 'b'},
            'permissions': ['read', 'write'],
            'hidePermissions': ['read', 'write'],
            'properties': {
                'subnets': [{'name': 'net1'}, {'name': 'net2'}],
                'adds': [[{'name': '0'}], [{'name': '0'}, {'name': '1'}, {'name': '2'}], [{'name': '2'}, {'name': '3'}]],
                'domains': {'a': {'name': '0'}, 'b': {'name': '1'}, 'c': {'name': '2'}},
                'conns': {'a': {'a1': {'name': '0'}, 'a2': {'name': '1'}}, 'b': {'b1': {'name': '3'}}}
            }
        }))

        return value

    def test_aaz_content_builder_for_update(self):
        from azure.cli.core.aaz._content_builder import AAZContentBuilder, AAZContentArgBrowser
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType

        _value = self._define_instance_value()

        _args_schema = self._define_args_schema()
        arg_value = _args_schema(data={})
        arg_value.name = 'b'

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
            args=[AAZContentArgBrowser(arg_value=arg_value, arg_data=arg_value.to_serialized_data())]
        )

        _builder.set_prop('name', AAZStrType, '.name')

        self.assertTrue(_value.to_serialized_data()['name'] == 'b')

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

        self.assertTrue(_value.to_serialized_data()['properties']['subnets'] == [
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

        self.assertTrue(_value.to_serialized_data()['properties']['adds'] == [
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

        self.assertTrue(_value.to_serialized_data()['properties']['domains'] == {
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

        self.assertTrue(_value.to_serialized_data()['properties']['conns'] == {
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

        self.assertTrue(_value.to_serialized_data() == {
            'name': 'b',
            'tags': {'tag_a': '2'},
            'hideTags': {'h_tag_a': '2', 'h_tag_b': 'b'},
            'permissions': ['write'],
            'hidePermissions': ['copy', 'write', 'delete'],
            'properties': {
                'subnets': [{'name': 'net'}, {'name': 'net2'}, {'name': 'net3'}],
                'adds': [[{'name': '0'}, {'name': '1'}], [{'name': '1'}, {'name': '2'}], [{'name': '2'}, {'name': '3'}], [{'name': '4'}]],
                'domains': {'a': {'name': 'a'}, 'b': {'name': '1'}, 'c': {'name': '2'}, 'd': {'name': 'd'}},
                'conns': {'a': {'f1': {'name': 'f1'}}, 'b': {'b1': {'name': 'b1'}, 'b3': {'name': 'b3'}}, 'd': {'d': {'name': 'd'}}}
            }
        })
