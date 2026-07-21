import collections
import copy
from .Utils import _write_complex_object

class RequestData(object):
    """Data contract class for type RequestData.
    """
    ENVELOPE_TYPE_NAME = 'Microsoft.ApplicationInsights.Request'	
    	
    DATA_TYPE_NAME = 'RequestData'

    _defaults = collections.OrderedDict([
        ('ver', 2),
        ('id', None),
        ('source', None),
        ('name', None),
        ('duration', None),
        ('responseCode', None),
        ('success', None),
        ('url', None),
        ('properties', {}),
        ('measurements', {})
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'ver': 2,
            'id': None,
            'duration': None,
            'responseCode': None,
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
    def source(self):
        """The source property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'source' in self._values:
            return self._values['source']
        return self._defaults['source']
        
    @source.setter
    def source(self, value):
        """The source property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['source'] and 'source' in self._values:
            del self._values['source']
        else:
            self._values['source'] = value
        
    @property
    def name(self):
        """The name property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'name' in self._values:
            return self._values['name']
        return self._defaults['name']
        
    @name.setter
    def name(self, value):
        """The name property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['name'] and 'name' in self._values:
            del self._values['name']
        else:
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
    def response_code(self):
        """The response_code property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        return self._values['responseCode']
        
    @response_code.setter
    def response_code(self, value):
        """The response_code property.
        
        Args:
            value (string). the property value.
        """
        self._values['responseCode'] = value
        
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
    def url(self):
        """The url property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'url' in self._values:
            return self._values['url']
        return self._defaults['url']
        
    @url.setter
    def url(self, value):
        """The url property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['url'] and 'url' in self._values:
            del self._values['url']
        else:
            self._values['url'] = value
        
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

