import collections
import copy
from .Utils import _write_complex_object

class Application(object):
    """Data contract class for type Application.
    """
    _defaults = collections.OrderedDict([
        ('ai.application.ver', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
        }
        self._initialize()
        
    @property
    def ver(self):
        """The ver property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.application.ver' in self._values:
            return self._values['ai.application.ver']
        return self._defaults['ai.application.ver']
        
    @ver.setter
    def ver(self, value):
        """The ver property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.application.ver'] and 'ai.application.ver' in self._values:
            del self._values['ai.application.ver']
        else:
            self._values['ai.application.ver'] = value
        
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

