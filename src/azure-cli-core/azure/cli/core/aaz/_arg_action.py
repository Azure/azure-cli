
from argparse import Action, ArgumentTypeError


class AAZArgAction(Action):

    _schema = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        data = self.format_data(values)
        setattr(namespace, self.dest, data)

    def format_data(self, data):
        """format input data"""
        # fill blank argument
        if data is None:
            return self._schema._blank
        return data


class AAZSimpleTypeArgAction(AAZArgAction):

    def format_data(self, data):
        data = super().format_data(data)
        if isinstance(data, str):
            if self._schema.enum:
                return self._schema.enum[data]
            else:
                return self._schema.DataType(data)
        elif isinstance(data, self._schema.DataType) or data is None:
            return data
        else:
            raise ArgumentTypeError(f"{self._schema.DataType} type value expected, got '{data}'({type(data)})")


class AAZObjectArgAction(AAZArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class AAZDictArgAction(AAZArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class AAZListArgAction(AAZArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        pass

