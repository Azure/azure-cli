import collections
import copy
from .Utils import _write_complex_object

class Internal(object):
    """Data contract class for type Internal.
    """
    _defaults = collections.OrderedDict([
        ('ai.internal.sdkVersion', None),
        ('ai.internal.agentVersion', None),
        ('ai.internal.nodeName', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
        }
        self._initialize()
        
    @property
    def sdk_version(self):
        """The sdk_version property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.internal.sdkVersion' in self._values:
            return self._values['ai.internal.sdkVersion']
        return self._defaults['ai.internal.sdkVersion']
        
    @sdk_version.setter
    def sdk_version(self, value):
        """The sdk_version property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.internal.sdkVersion'] and 'ai.internal.sdkVersion' in self._values:
            del self._values['ai.internal.sdkVersion']
        else:
            self._values['ai.internal.sdkVersion'] = value
        
    @property
    def agent_version(self):
        """The agent_version property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.internal.agentVersion' in self._values:
            return self._values['ai.internal.agentVersion']
        return self._defaults['ai.internal.agentVersion']
        
    @agent_version.setter
    def agent_version(self, value):
        """The agent_version property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.internal.agentVersion'] and 'ai.internal.agentVersion' in self._values:
            del self._values['ai.internal.agentVersion']
        else:
            self._values['ai.internal.agentVersion'] = value
        
    @property
    def node_name(self):
        """The node_name property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.internal.nodeName' in self._values:
            return self._values['ai.internal.nodeName']
        return self._defaults['ai.internal.nodeName']
        
    @node_name.setter
    def node_name(self, value):
        """The node_name property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.internal.nodeName'] and 'ai.internal.nodeName' in self._values:
            del self._values['ai.internal.nodeName']
        else:
            self._values['ai.internal.nodeName'] = value
        
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

