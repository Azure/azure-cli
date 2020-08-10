import collections
import copy
from .Utils import _write_complex_object

class Base(object):
    """Data contract class for type Base.
    """
    _defaults = collections.OrderedDict([
        ('baseType', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
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

