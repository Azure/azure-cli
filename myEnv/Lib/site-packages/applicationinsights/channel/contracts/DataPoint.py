import collections
import copy
from .Utils import _write_complex_object
from .DataPointType import DataPointType

class DataPoint(object):
    """Data contract class for type DataPoint.
    """
    _defaults = collections.OrderedDict([
        ('ns', None),
        ('name', None),
        ('kind', DataPointType.measurement),
        ('value', None),
        ('count', None),
        ('min', None),
        ('max', None),
        ('stdDev', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'name': None,
            'kind': DataPointType.measurement,
            'value': None,
        }
        self._initialize()
        
    @property
    def ns(self):
        """The ns property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ns' in self._values:
            return self._values['ns']
        return self._defaults['ns']
        
    @ns.setter
    def ns(self, value):
        """The ns property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ns'] and 'ns' in self._values:
            del self._values['ns']
        else:
            self._values['ns'] = value
        
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
    def kind(self):
        """The kind property.
        
        Returns:
            (:class:`DataPointType.measurement`). the property value. (defaults to: DataPointType.measurement)
        """
        if 'kind' in self._values:
            return self._values['kind']
        return self._defaults['kind']
        
    @kind.setter
    def kind(self, value):
        """The kind property.
        
        Args:
            value (:class:`DataPointType.measurement`). the property value.
        """
        if value == self._defaults['kind'] and 'kind' in self._values:
            del self._values['kind']
        else:
            self._values['kind'] = value
        
    @property
    def value(self):
        """The value property.
        
        Returns:
            (float). the property value. (defaults to: None)
        """
        return self._values['value']
        
    @value.setter
    def value(self, value):
        """The value property.
        
        Args:
            value (float). the property value.
        """
        self._values['value'] = value
        
    @property
    def count(self):
        """The count property.
        
        Returns:
            (int). the property value. (defaults to: None)
        """
        if 'count' in self._values:
            return self._values['count']
        return self._defaults['count']
        
    @count.setter
    def count(self, value):
        """The count property.
        
        Args:
            value (int). the property value.
        """
        if value == self._defaults['count'] and 'count' in self._values:
            del self._values['count']
        else:
            self._values['count'] = value
        
    @property
    def min(self):
        """The min property.
        
        Returns:
            (float). the property value. (defaults to: None)
        """
        if 'min' in self._values:
            return self._values['min']
        return self._defaults['min']
        
    @min.setter
    def min(self, value):
        """The min property.
        
        Args:
            value (float). the property value.
        """
        if value == self._defaults['min'] and 'min' in self._values:
            del self._values['min']
        else:
            self._values['min'] = value
        
    @property
    def max(self):
        """The max property.
        
        Returns:
            (float). the property value. (defaults to: None)
        """
        if 'max' in self._values:
            return self._values['max']
        return self._defaults['max']
        
    @max.setter
    def max(self, value):
        """The max property.
        
        Args:
            value (float). the property value.
        """
        if value == self._defaults['max'] and 'max' in self._values:
            del self._values['max']
        else:
            self._values['max'] = value
        
    @property
    def std_dev(self):
        """The std_dev property.
        
        Returns:
            (float). the property value. (defaults to: None)
        """
        if 'stdDev' in self._values:
            return self._values['stdDev']
        return self._defaults['stdDev']
        
    @std_dev.setter
    def std_dev(self, value):
        """The std_dev property.
        
        Args:
            value (float). the property value.
        """
        if value == self._defaults['stdDev'] and 'stdDev' in self._values:
            del self._values['stdDev']
        else:
            self._values['stdDev'] = value
        
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

