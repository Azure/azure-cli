import argparse


class MetaDataAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        namespace.metadata = self.get_action(values)

    def get_action(self, values):
        properties = dict()
        for (k, v) in (x.split('=', 1) for x in values):
            properties[k] = v
        return properties
        