import collections
import copy
from .Utils import _write_complex_object

class RemoteDependencyData(object):
    """Data contract class for type RemoteDependencyData.
    """
    ENVELOPE_TYPE_NAME = 'Microsoft.ApplicationInsights.RemoteDependency'	
    	
    DATA_TYPE_NAME = 'RemoteDependencyData'

    _defaults = collections.OrderedDict([
        ('ver', 2),
        ('name', None),
        ('id', None),
        ('resultCode', None),
        ('duration', None),
        ('success', True),
        ('data', None),
        ('target', None),
        ('type', None),
        ('properties', {}),
        ('measurements', {})
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'ver': 2,
            'name': None,
            'duration': None,
            'success': True,
        }
        self._initialize()
        
    @property
    def ver(self):
        """The ver property.
        
        Returns:
            (int). the property value. (defaults to: 2)
        """
        return self._values['ver']
        
    @ver.setter
    def ver(self, value):
        """The ver property.
        
        Args:
            value (int). the property value.
        """
        self._values['ver'] = value
        
    @property
    def name(self):
        """The name property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        return self._values['name']
        
    @name.setter
    def name(self, value):
        """The name property.
        
        Args:
            value (string). the property value.
        """
        self._values['name'] = value
        
    @property
    def id(self):
        """The id property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'id' in self._values:
            return self._values['id']
        return self._defaults['id']
        
    @id.setter
    def id(self, value):
        """The id property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['id'] and 'id' in self._values:
            del self._values['id']
        else:
            self._values['id'] = value
        
    @property
    def result_code(self):
        """The result_code property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'resultCode' in self._values:
            return self._values['resultCode']
        return self._defaults['resultCode']
        
    @result_code.setter
    def result_code(self, value):
        """The result_code property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['resultCode'] and 'resultCode' in self._values:
            del self._values['resultCode']
        else:
            self._values['resultCode'] = value
        
    @property
    def duration(self):
        """The duration property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        return self._values['duration']
        
    @duration.setter
    def duration(self, value):
        """The duration property.
        
        Args:
            value (string). the property value.
        """
        self._values['duration'] = value
        
    @property
    def success(self):
        """The success property.
        
        Returns:
            (bool). the property value. (defaults to: True)
        """
        if 'success' in self._values:
            return self._values['success']
        return self._defaults['success']
        
    @success.setter
    def success(self, value):
        """The success property.
        
        Args:
            value (bool). the property value.
        """
        if value == self._defaults['success'] and 'success' in self._values:
            del self._values['success']
        else:
            self._values['success'] = value
        
    @property
    def data(self):
        """The data property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'data' in self._values:
            return self._values['data']
        return self._defaults['data']
        
    @data.setter
    def data(self, value):
        """The data property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['data'] and 'data' in self._values:
            del self._values['data']
        else:
            self._values['data'] = value
        
    @property
    def target(self):
        """The target property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'target' in self._values:
            return self._values['target']
        return self._defaults['target']
        
    @target.setter
    def target(self, value):
        """The target property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['target'] and 'target' in self._values:
            del self._values['target']
        else:
            self._values['target'] = value
        
    @property
    def type(self):
        """The type property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'type' in self._values:
            return self._values['type']
        return self._defaults['type']
        
    @type.setter
    def type(self, value):
        """The type property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['type'] and 'type' in self._values:
            del self._values['type']
        else:
            self._values['type'] = value
        
    @property
    def properties(self):
        """The properties property.
        
        Returns:
            (hash). the property value. (defaults to: {})
        """
        if 'properties' in self._values:
            return self._values['properties']
        self._values['properties'] = copy.deepcopy(self._defaults['properties'])
        return self._values['properties']
        
    @properties.setter
    def properties(self, value):
        """The properties property.
        
        Args:
            value (hash). the property value.
        """
        if value == self._defaults['properties'] and 'properties' in self._values:
            del self._values['properties']
        else:
            self._values['properties'] = value
        
    @property
    def measurements(self):
        """The measurements property.
        
        Returns:
            (hash). the property value. (defaults to: {})
        """
        if 'measurements' in self._values:
            return self._values['measurements']
        self._values['measurements'] = copy.deepcopy(self._defaults['measurements'])
        return self._values['measurements']
        
    @measurements.setter
    def measurements(self, value):
        """The measurements property.
        
        Args:
            value (hash). the property value.
        """
        if value == self._defaults['measurements'] and 'measurements' in self._values:
            del self._values['measurements']
        else:
            self._values['measurements'] = value
        
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

