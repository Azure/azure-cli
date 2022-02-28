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
                    "b1": "3"
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
        _builder.set_prop('hidePermissions', AAZDictType, '.h_permissions')

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

        elements = _builder.get('.properties.conns[]')
        if elements:
            elements.set_elements(AAZObjectType)

        elements = _builder.get('.properties.conns[][]')
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

    def test_aaz_content_builder_for_update(self):
        from azure.cli.core.aaz._content_builder import AAZContentBuilder, AAZContentArgBrowser
        from azure.cli.core.aaz._field_type import AAZStrType, AAZObjectType, AAZListType, AAZDictType

        _args_schema = self._define_args_schema()
        pass

