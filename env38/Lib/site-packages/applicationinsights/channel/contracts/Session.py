import collections
import copy
from .Utils import _write_complex_object

class Session(object):
    """Data contract class for type Session.
    """
    _defaults = collections.OrderedDict([
        ('ai.session.id', None),
        ('ai.session.isFirst', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
        }
        self._initialize()
        
    @property
    def id(self):
        """The id property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.session.id' in self._values:
            return self._values['ai.session.id']
        return self._defaults['ai.session.id']
        
    @id.setter
    def id(self, value):
        """The id property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.session.id'] and 'ai.session.id' in self._values:
            del self._values['ai.session.id']
        else:
            self._values['ai.session.id'] = value
        
    @property
    def is_first(self):
        """The is_first property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.session.isFirst' in self._values:
            return self._values['ai.session.isFirst']
        return self._defaults['ai.session.isFirst']
        
    @is_first.setter
    def is_first(self, value):
        """The is_first property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.session.isFirst'] and 'ai.session.isFirst' in self._values:
            del self._values['ai.session.isFirst']
        else:
            self._values['ai.session.isFirst'] = value
        
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

