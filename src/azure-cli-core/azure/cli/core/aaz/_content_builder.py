from ._base import AAZBaseValue, AAZUndefined
from ._field_value import AAZSimpleValue, AAZDict, AAZList, AAZObject
from ._arg_browser import AAZArgBrowser


class AAZContentBuilder:

    def __init__(self, values, args):
        assert len(args) > 0
        for arg in args:
            assert isinstance(arg, AAZArgBrowser)
        assert len(values) == len(args)
        for value in values:
            assert isinstance(value, AAZBaseValue)
        self._values = values
        self._args = args
        self._sub_prop_builders = {}
        self._sub_elements_builder = None

    def set_prop(self, prop_name, typ, arg_key=None):
        sub_values = []
        sub_args = []
        for value, arg in zip(self._values, self._args):
            schema = value._schema
            sub_arg = arg.get_prop(arg_key)
            if sub_arg is not None and sub_arg.data != AAZUndefined:
                if schema.get_attr_name(prop_name) is None:
                    schema[prop_name] = typ()
                else:
                    assert isinstance(schema[prop_name], typ)
                if not sub_arg.is_patch and arg_key:
                    if isinstance(value[prop_name], AAZSimpleValue):
                        value[prop_name] = sub_arg.data
                    elif isinstance(value[prop_name], AAZList):
                        value[prop_name] = []
                    elif isinstance(value[prop_name], (AAZDict, AAZObject)):
                        value[prop_name] = {}
                    else:
                        raise NotImplementedError()
                sub_values.append(value[prop_name])
                sub_args.append(sub_arg)

        if sub_values:
            self._sub_prop_builders[prop_name] = AAZContentBuilder(sub_values, sub_args)
            return self._sub_prop_builders[prop_name]
        else:
            return None

    def set_elements(self, typ, arg_key=None):
        sub_values = []
        sub_args = []
        for value, arg in zip(self._values, self._args):
            schema = value._schema
            if schema._element is None:
                schema.Element = typ()
            else:
                assert isinstance(schema.Element, typ)
            if isinstance(value, (AAZDict, AAZList)):
                for key, sub_arg in arg.get_elements():
                    if sub_arg is not None and sub_arg.data != AAZUndefined:
                        sub_arg = sub_arg.get_prop(arg_key)

                    if sub_arg is not None and sub_arg.data != AAZUndefined:
                        if not sub_arg.is_patch and arg_key:
                            if isinstance(value[key], AAZSimpleValue):
                                value[key] = sub_arg.data
                            elif isinstance(value[key], AAZList):
                                value[key] = []
                            elif isinstance(value[key], (AAZDict, AAZObject)):
                                value[key] = {}
                            else:
                                raise NotImplementedError()
                        sub_values.append(value[key])
                        sub_args.append(sub_arg)
            else:
                raise NotImplementedError()

        if sub_values:
            self._sub_elements_builder = AAZContentBuilder(sub_values, sub_args)
            return self._sub_elements_builder
        else:
            return None

    def get(self, key):
        if not key or key == '.':
            return self
        parts = [part for part in key.replace('[', '.[').replace('{', '.{').split('.') if part]

        return self._get(*parts)

    def _get(self, *key_parts):
        if not key_parts:
            return self
        if key_parts[0] == '[]':
            # list elements builder
            if not self._sub_elements_builder:
                return None
            sub_builder = self._sub_elements_builder
        elif key_parts[0] == '{}':
            # dict elements builder
            if not self._sub_elements_builder:
                return None
            sub_builder = self._sub_elements_builder
        else:
            if key_parts[0] not in self._sub_prop_builders:
                return None
            sub_builder = self._sub_prop_builders[key_parts[0]]
        return sub_builder._get(*key_parts[1:])
