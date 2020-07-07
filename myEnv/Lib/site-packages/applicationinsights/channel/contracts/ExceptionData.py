import collections
import copy
from .Utils import _write_complex_object

class ExceptionData(object):
    """Data contract class for type ExceptionData.
    """

    ENVELOPE_TYPE_NAME = 'Microsoft.ApplicationInsights.Exception'	
    	
    DATA_TYPE_NAME = 'ExceptionData'

    _defaults = collections.OrderedDict([
        ('ver', 2),
        ('exceptions', []),
        ('severityLevel', None),
        ('problemId', None),
        ('properties', {}),
        ('measurements', {})
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'ver': 2,
            'exceptions': [],
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
    def exceptions(self):
        """The exceptions property.
        
        Returns:
            (list). the property value. (defaults to: [])
        """
        return self._values['exceptions']
        
    @exceptions.setter
    def exceptions(self, value):
        """The exceptions property.
        
        Args:
            value (list). the property value.
        """
        self._values['exceptions'] = value
        
    @property
    def severity_level(self):
        """The severity_level property.
        
        Returns:
            (int). the property value. (defaults to: None)
        """
        if 'severityLevel' in self._values:
            return self._values['severityLevel']
        return self._defaults['severityLevel']
        
    @severity_level.setter
    def severity_level(self, value):
        """The severity_level property.
        
        Args:
            value (int). the property value.
        """
        if value == self._defaults['severityLevel'] and 'severityLevel' in self._values:
            del self._values['severityLevel']
        else:
            self._values['severityLevel'] = value
        
    @property
    def problem_id(self):
        """The problem_id property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'problemId' in self._values:
            return self._values['problemId']
        return self._defaults['problemId']
        
    @problem_id.setter
    def problem_id(self, value):
        """The problem_id property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['problemId'] and 'problemId' in self._values:
            del self._values['problemId']
        else:
            self._values['problemId'] = value
        
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

