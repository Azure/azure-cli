import collections
import copy
from .Utils import _write_complex_object

class PageViewPerfData(object):
    """Data contract class for type PageViewPerfData.
    """
    ENVELOPE_TYPE_NAME = 'Microsoft.ApplicationInsights.PageViewPerfData'	
    	
    DATA_TYPE_NAME = 'PageViewPerfData'

    _defaults = collections.OrderedDict([
        ('ver', 2),
        ('ver', 2),
        ('url', None),
        ('perfTotal', None),
        ('name', None),
        ('name', None),
        ('duration', None),
        ('networkConnect', None),
        ('sentRequest', None),
        ('receivedResponse', None),
        ('id', None),
        ('domProcessing', None),
        ('referrerUri', None),
        ('properties', {}),
        ('properties', {}),
        ('measurements', {}),
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
    def perf_total(self):
        """The perf_total property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'perfTotal' in self._values:
            return self._values['perfTotal']
        return self._defaults['perfTotal']
        
    @perf_total.setter
    def perf_total(self, value):
        """The perf_total property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['perfTotal'] and 'perfTotal' in self._values:
            del self._values['perfTotal']
        else:
            self._values['perfTotal'] = value
        
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
        if 'duration' in self._values:
            return self._values['duration']
        return self._defaults['duration']
        
    @duration.setter
    def duration(self, value):
        """The duration property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['duration'] and 'duration' in self._values:
            del self._values['duration']
        else:
            self._values['duration'] = value
        
    @property
    def network_connect(self):
        """The network_connect property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'networkConnect' in self._values:
            return self._values['networkConnect']
        return self._defaults['networkConnect']
        
    @network_connect.setter
    def network_connect(self, value):
        """The network_connect property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['networkConnect'] and 'networkConnect' in self._values:
            del self._values['networkConnect']
        else:
            self._values['networkConnect'] = value
        
    @property
    def sent_request(self):
        """The sent_request property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'sentRequest' in self._values:
            return self._values['sentRequest']
        return self._defaults['sentRequest']
        
    @sent_request.setter
    def sent_request(self, value):
        """The sent_request property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['sentRequest'] and 'sentRequest' in self._values:
            del self._values['sentRequest']
        else:
            self._values['sentRequest'] = value
        
    @property
    def received_response(self):
        """The received_response property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'receivedResponse' in self._values:
            return self._values['receivedResponse']
        return self._defaults['receivedResponse']
        
    @received_response.setter
    def received_response(self, value):
        """The received_response property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['receivedResponse'] and 'receivedResponse' in self._values:
            del self._values['receivedResponse']
        else:
            self._values['receivedResponse'] = value
        
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
    def dom_processing(self):
        """The dom_processing property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'domProcessing' in self._values:
            return self._values['domProcessing']
        return self._defaults['domProcessing']
        
    @dom_processing.setter
    def dom_processing(self, value):
        """The dom_processing property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['domProcessing'] and 'domProcessing' in self._values:
            del self._values['domProcessing']
        else:
            self._values['domProcessing'] = value
        
    @property
    def referrer_uri(self):
        """The referrer_uri property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'referrerUri' in self._values:
            return self._values['referrerUri']
        return self._defaults['referrerUri']
        
    @referrer_uri.setter
    def referrer_uri(self, value):
        """The referrer_uri property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['referrerUri'] and 'referrerUri' in self._values:
            del self._values['referrerUri']
        else:
            self._values['referrerUri'] = value
        
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

