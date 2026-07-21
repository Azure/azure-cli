import collections
import copy
from .Utils import _write_complex_object

class AvailabilityData(object):
    """Data contract class for type AvailabilityData.
    """
    _defaults = collections.OrderedDict([
        ('ver', 2),
        ('id', None),
        ('name', None),
        ('duration', None),
        ('success', None),
        ('runLocation', None),
        ('message', None),
        ('properties', {}),
        ('measurements', {})
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'ver': 2,
            'id': None,
            'name': None,
            'duration': None,
            'success': None,
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
    def id(self):
        """The id property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        return self._values['id']
        
    @id.setter
    def id(self, value):
        """The id property.
        
        Args:
            value (string). the property value.
        """
        self._values['id'] = value
        
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
            (bool). the property value. (defaults to: None)
        """
        return self._values['success']
        
    @success.setter
    def success(self, value):
        """The success property.
        
        Args:
            value (bool). the property value.
        """
        self._values['success'] = value
        
    @property
    def run_location(self):
        """The run_location property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'runLocation' in self._values:
            return self._values['runLocation']
        return self._defaults['runLocation']
        
    @run_location.setter
    def run_location(self, value):
        """The run_location property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['runLocation'] and 'runLocation' in self._values:
            del self._values['runLocation']
        else:
            self._values['runLocation'] = value
        
    @property
    def message(self):
        """The message property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'message' in self._values:
            return self._values['message']
        return self._defaults['message']
        
    @message.setter
    def message(self, value):
        """The message property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['message'] and 'message' in self._values:
            del self._values['message']
        else:
            self._values['message'] = value
        
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

