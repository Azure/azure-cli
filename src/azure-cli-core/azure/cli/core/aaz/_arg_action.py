
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
        if isinstance(data, self._schema._data_type) or data is None:
            return data
        else:
            if not isinstance(data, str):
                raise ArgumentTypeError(f"{self._schema._data_type} type value expected, got '{data}'({type(data)})")
            return self._schema._data_type(data)


class AAZBoolArgAction(AAZArgAction):

    def format_data(self, data):
        data = super().format_data(data)
        if isinstance(data, bool) or data is None:
            return data
        else:
            if not isinstance(data, str):
                raise ArgumentTypeError(f"bool type value expected, got '{data}'({type(data)})")
            if data.lower() in ('true', 't', 'yes', 'y', '1'):
                return True
            elif data.lower() in ('false',  'f', 'no', 'n', '0'):
                return False
            else:
                raise ArgumentTypeError(f"bool type value expected, got '{data}'({type(data)})")
