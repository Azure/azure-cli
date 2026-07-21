import collections
import copy
from .Utils import _write_complex_object

class EventData(object):
    """Data contract class for type EventData.
    """
    
    ENVELOPE_TYPE_NAME = 'Microsoft.ApplicationInsights.Event'	
    	
    DATA_TYPE_NAME = 'EventData'	
        
    _defaults = collections.OrderedDict([
        ('ver', 2),
        ('name', None),
        ('properties', {}),
        ('measurements', {})
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'ver': 2,
            'name': None,
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

