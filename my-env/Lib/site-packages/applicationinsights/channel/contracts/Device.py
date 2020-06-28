import collections
import copy
from .Utils import _write_complex_object

class Device(object):
    """Data contract class for type Device.
    """
    _defaults = collections.OrderedDict([
        ('ai.device.id', None),
        ('ai.device.locale', None),
        ('ai.device.model', None),
        ('ai.device.oemName', None),
        ('ai.device.osVersion', None),
        ('ai.device.type', None)
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
        if 'ai.device.id' in self._values:
            return self._values['ai.device.id']
        return self._defaults['ai.device.id']
        
    @id.setter
    def id(self, value):
        """The id property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.device.id'] and 'ai.device.id' in self._values:
            del self._values['ai.device.id']
        else:
            self._values['ai.device.id'] = value
        
    @property
    def locale(self):
        """The locale property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.device.locale' in self._values:
            return self._values['ai.device.locale']
        return self._defaults['ai.device.locale']
        
    @locale.setter
    def locale(self, value):
        """The locale property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.device.locale'] and 'ai.device.locale' in self._values:
            del self._values['ai.device.locale']
        else:
            self._values['ai.device.locale'] = value
        
    @property
    def model(self):
        """The model property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.device.model' in self._values:
            return self._values['ai.device.model']
        return self._defaults['ai.device.model']
        
    @model.setter
    def model(self, value):
        """The model property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.device.model'] and 'ai.device.model' in self._values:
            del self._values['ai.device.model']
        else:
            self._values['ai.device.model'] = value
        
    @property
    def oem_name(self):
        """The oem_name property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.device.oemName' in self._values:
            return self._values['ai.device.oemName']
        return self._defaults['ai.device.oemName']
        
    @oem_name.setter
    def oem_name(self, value):
        """The oem_name property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.device.oemName'] and 'ai.device.oemName' in self._values:
            del self._values['ai.device.oemName']
        else:
            self._values['ai.device.oemName'] = value
        
    @property
    def os_version(self):
        """The os_version property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.device.osVersion' in self._values:
            return self._values['ai.device.osVersion']
        return self._defaults['ai.device.osVersion']
        
    @os_version.setter
    def os_version(self, value):
        """The os_version property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.device.osVersion'] and 'ai.device.osVersion' in self._values:
            del self._values['ai.device.osVersion']
        else:
            self._values['ai.device.osVersion'] = value
        
    @property
    def type(self):
        """The type property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.device.type' in self._values:
            return self._values['ai.device.type']
        return self._defaults['ai.device.type']
        
    @type.setter
    def type(self, value):
        """The type property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.device.type'] and 'ai.device.type' in self._values:
            del self._values['ai.device.type']
        else:
            self._values['ai.device.type'] = value
        
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

