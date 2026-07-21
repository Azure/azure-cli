import collections
import copy
from .Utils import _write_complex_object

class ExceptionDetails(object):
    """Data contract class for type ExceptionDetails.
    """
    _defaults = collections.OrderedDict([
        ('id', None),
        ('outerId', None),
        ('typeName', None),
        ('message', None),
        ('hasFullStack', True),
        ('stack', None),
        ('parsedStack', [])
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'typeName': None,
            'message': None,
            'hasFullStack': True,
        }
        self._initialize()
        
    @property
    def id(self):
        """The id property.
        
        Returns:
            (int). the property value. (defaults to: None)
        """
        if 'id' in self._values:
            return self._values['id']
        return self._defaults['id']
        
    @id.setter
    def id(self, value):
        """The id property.
        
        Args:
            value (int). the property value.
        """
        if value == self._defaults['id'] and 'id' in self._values:
            del self._values['id']
        else:
            self._values['id'] = value
        
    @property
    def outer_id(self):
        """The outer_id property.
        
        Returns:
            (int). the property value. (defaults to: None)
        """
        if 'outerId' in self._values:
            return self._values['outerId']
        return self._defaults['outerId']
        
    @outer_id.setter
    def outer_id(self, value):
        """The outer_id property.
        
        Args:
            value (int). the property value.
        """
        if value == self._defaults['outerId'] and 'outerId' in self._values:
            del self._values['outerId']
        else:
            self._values['outerId'] = value
        
    @property
    def type_name(self):
        """The type_name property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        return self._values['typeName']
        
    @type_name.setter
    def type_name(self, value):
        """The type_name property.
        
        Args:
            value (string). the property value.
        """
        self._values['typeName'] = value
        
    @property
    def message(self):
        """The message property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        return self._values['message']
        
    @message.setter
    def message(self, value):
        """The message property.
        
        Args:
            value (string). the property value.
        """
        self._values['message'] = value
        
    @property
    def has_full_stack(self):
        """The has_full_stack property.
        
        Returns:
            (bool). the property value. (defaults to: True)
        """
        if 'hasFullStack' in self._values:
            return self._values['hasFullStack']
        return self._defaults['hasFullStack']
        
    @has_full_stack.setter
    def has_full_stack(self, value):
        """The has_full_stack property.
        
        Args:
            value (bool). the property value.
        """
        if value == self._defaults['hasFullStack'] and 'hasFullStack' in self._values:
            del self._values['hasFullStack']
        else:
            self._values['hasFullStack'] = value
        
    @property
    def stack(self):
        """The stack property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'stack' in self._values:
            return self._values['stack']
        return self._defaults['stack']
        
    @stack.setter
    def stack(self, value):
        """The stack property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['stack'] and 'stack' in self._values:
            del self._values['stack']
        else:
            self._values['stack'] = value
        
    @property
    def parsed_stack(self):
        """The parsed_stack property.
        
        Returns:
            (list). the property value. (defaults to: [])
        """
        if 'parsedStack' in self._values:
            return self._values['parsedStack']
        self._values['parsedStack'] = copy.deepcopy(self._defaults['parsedStack'])
        return self._values['parsedStack']
        
    @parsed_stack.setter
    def parsed_stack(self, value):
        """The parsed_stack property.
        
        Args:
            value (list). the property value.
        """
        if value == self._defaults['parsedStack'] and 'parsedStack' in self._values:
            del self._values['parsedStack']
        else:
            self._values['parsedStack'] = value
        
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

