import collections
import copy
from .Utils import _write_complex_object

class Envelope(object):
    """Data contract class for type Envelope.
    """
    _defaults = collections.OrderedDict([
        ('ver', 1),
        ('name', None),
        ('time', None),
        ('sampleRate', 100.0),
        ('seq', None),
        ('iKey', None),
        ('tags', {}),
        ('data', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
            'ver': 1,
            'name': None,
            'time': None,
            'sampleRate': 100.0,
        }
        self._initialize()
        
    @property
    def ver(self):
        """The ver property.
        
        Returns:
            (int). the property value. (defaults to: 1)
        """
        if 'ver' in self._values:
            return self._values['ver']
        return self._defaults['ver']
        
    @ver.setter
    def ver(self, value):
        """The ver property.
        
        Args:
            value (int). the property value.
        """
        if value == self._defaults['ver'] and 'ver' in self._values:
            del self._values['ver']
        else:
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
    def time(self):
        """The time property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        return self._values['time']
        
    @time.setter
    def time(self, value):
        """The time property.
        
        Args:
            value (string). the property value.
        """
        self._values['time'] = value
        
    @property
    def sample_rate(self):
        """The sample_rate property.
        
        Returns:
            (float). the property value. (defaults to: 100.0)
        """
        if 'sampleRate' in self._values:
            return self._values['sampleRate']
        return self._defaults['sampleRate']
        
    @sample_rate.setter
    def sample_rate(self, value):
        """The sample_rate property.
        
        Args:
            value (float). the property value.
        """
        if value == self._defaults['sampleRate'] and 'sampleRate' in self._values:
            del self._values['sampleRate']
        else:
            self._values['sampleRate'] = value
        
    @property
    def seq(self):
        """The seq property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'seq' in self._values:
            return self._values['seq']
        return self._defaults['seq']
        
    @seq.setter
    def seq(self, value):
        """The seq property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['seq'] and 'seq' in self._values:
            del self._values['seq']
        else:
            self._values['seq'] = value
        
    @property
    def ikey(self):
        """The ikey property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'iKey' in self._values:
            return self._values['iKey']
        return self._defaults['iKey']
        
    @ikey.setter
    def ikey(self, value):
        """The ikey property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['iKey'] and 'iKey' in self._values:
            del self._values['iKey']
        else:
            self._values['iKey'] = value
        
    @property
    def tags(self):
        """The tags property.
        
        Returns:
            (hash). the property value. (defaults to: {})
        """
        if 'tags' in self._values:
            return self._values['tags']
        self._values['tags'] = copy.deepcopy(self._defaults['tags'])
        return self._values['tags']
        
    @tags.setter
    def tags(self, value):
        """The tags property.
        
        Args:
            value (hash). the property value.
        """
        if value == self._defaults['tags'] and 'tags' in self._values:
            del self._values['tags']
        else:
            self._values['tags'] = value
        
    @property
    def data(self):
        """The data property.
        
        Returns:
            (object). the property value. (defaults to: None)
        """
        if 'data' in self._values:
            return self._values['data']
        return self._defaults['data']
        
    @data.setter
    def data(self, value):
        """The data property.
        
        Args:
            value (object). the property value.
        """
        if value == self._defaults['data'] and 'data' in self._values:
            del self._values['data']
        else:
            self._values['data'] = value
        
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

