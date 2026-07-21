import collections
import copy
from .Utils import _write_complex_object

class Location(object):
    """Data contract class for type Location.
    """
    _defaults = collections.OrderedDict([
        ('ai.location.ip', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
        }
        self._initialize()
        
    @property
    def ip(self):
        """The ip property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.location.ip' in self._values:
            return self._values['ai.location.ip']
        return self._defaults['ai.location.ip']
        
    @ip.setter
    def ip(self, value):
        """The ip property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.location.ip'] and 'ai.location.ip' in self._values:
            del self._values['ai.location.ip']
        else:
            self._values['ai.location.ip'] = value
        
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

