import collections
import copy
from .Utils import _write_complex_object

class Data(object):
    """Data contract class for type Data.
    """
    _defaults = collections.OrderedDict([
        ('baseType', None),
        ('baseData', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'baseData': None
        }
        self._initialize()
        
    @property
    def base_type(self):
        """The base_type property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'baseType' in self._values:
            return self._values['baseType']
        return self._defaults['baseType']
        
    @base_type.setter
    def base_type(self, value):
        """The base_type property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['baseType'] and 'baseType' in self._values:
            del self._values['baseType']
        else:
            self._values['baseType'] = value
        
    @property
    def base_data(self):
        """The base_data property.
        
        Returns:
            (object). the property value. (defaults to: None)
        """
        return self._values['baseData']
        
    @base_data.setter
    def base_data(self, value):
        """The base_data property.
        
        Args:
            value (object). the property value.
        """
        self._values['baseData'] = value
        
    def _initialize(self):
        """Initializes the current instance of the object.
        """
        pass
    
    def write(self):
        """Writes the contents of this object and returns the content as a dict object.
        
        Returns:
            (dict). the object that represents the same data as the current instance.
        """
        return _write_complex_object(self._defaults, self._values)

