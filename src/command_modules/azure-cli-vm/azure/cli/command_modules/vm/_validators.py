class MinMaxValue(object): # pylint: disable=too-few-public-methods
    '''Converter/validator for range type values. Intended use is as the type parameter
    for argparse options
    '''
    def __init__(self, min_value, max_value, value_type=int):
        self.min_value = min_value
        self.max_value = max_value
        self.value_type = value_type

    def __call__(self, strvalue):
        value = self.value_type(strvalue)
        if value < self.min_value or value > self.max_value:
            raise ValueError()
        return value

    def __repr__(self):
        '''Used by argparse to display error messages
        '''
        return 'value. Valid values: %s - %s, given' % (str(self.min_value), str(self.max_value))