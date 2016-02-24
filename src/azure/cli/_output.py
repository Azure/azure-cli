"""
Manage output for the CLI
"""
import sys
import json

from enum import Enum

from azure.cli._util import TableOutput, TextOutput

class OutputFormats(Enum):
    """
    The output formats supported by this module
    """
    JSON = 1
    TABLE = 2
    TEXT = 3

class OutputProducer(object):
    """
    Produce output for the CLI
    """
    
    def __init__(self, format=OutputFormats.JSON, file=sys.stdout):
        """Constructor.
        
        Keyword arguments:
        format -- the output format to use
        file   -- the file object to use when printing
        """
        if format not in OutputFormats:
            raise OutputFormatException("Unknown format {0}".format(format))
        self.format = format
        # get the formatter
        if self.format is OutputFormats.JSON:
            self.formatter = JSONFormatter()
        elif self.format is OutputFormats.TABLE:
            self.formatter = TableFormatter()
        elif self.format is OutputFormats.TEXT:
            self.formatter = TextFormatter()
        self.file = file

    def out(self, obj):
        print(self.formatter(obj), file=self.file)

class JSONFormatter(object):

    def __init__(self):
        # can pass in configuration if needed
        pass
        
    def __call__(self, obj):
        input_dict = obj.__dict__ if hasattr(obj, '__dict__') else obj
        return json.dumps(input_dict, indent=4, sort_keys=True)

class TableFormatter(object):

    def __init__(self):
        # can pass in configuration if needed
        pass
        
    def __call__(self, obj):
        obj_list = obj if isinstance(obj, list) else [obj]
        with TableOutput() as to:
            try:
                for item in obj_list:
                    for item_key in sorted(item):
                        to.cell(item_key, item[item_key])
                    to.end_row()
                return to.dump()
            except TypeError:
                return ''

class TextFormatter(object):

    def __init__(self):
        # can pass in configuration if needed
        pass
        
    def __call__(self, obj):
        obj_list = obj if isinstance(obj, list) else [obj]
        with TextOutput() as to:
            try:
                for item in obj_list:
                    for item_key in sorted(item):
                        to.add(item_key, item[item_key])
                return to.dump()
            except TypeError:
                return ''

class OutputFormatException(Exception):
    """The output format specified is not recognized.
    """
    pass
