import collections
import copy
from .Utils import _write_complex_object

class Cloud(object):
    """Data contract class for type Cloud.
    """
    _defaults = collections.OrderedDict([
        ('ai.cloud.role', None),
        ('ai.cloud.roleInstance', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
        }
        self._initialize()
        
    @property
    def role(self):
        """The role property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.cloud.role' in self._values:
            return self._values['ai.cloud.role']
        return self._defaults['ai.cloud.role']
        
    @role.setter
    def role(self, value):
        """The role property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.cloud.role'] and 'ai.cloud.role' in self._values:
            del self._values['ai.cloud.role']
        else:
            self._values['ai.cloud.role'] = value
        
    @property
    def role_instance(self):
        """The role_instance property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.cloud.roleInstance' in self._values:
            return self._values['ai.cloud.roleInstance']
        return self._defaults['ai.cloud.roleInstance']
        
    @role_instance.setter
    def role_instance(self, value):
        """The role_instance property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.cloud.roleInstance'] and 'ai.cloud.roleInstance' in self._values:
            del self._values['ai.cloud.roleInstance']
        else:
            self._values['ai.cloud.roleInstance'] = value
        
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

