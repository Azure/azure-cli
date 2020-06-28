import collections
import copy
from .Utils import _write_complex_object

class User(object):
    """Data contract class for type User.
    """
    _defaults = collections.OrderedDict([
        ('ai.user.accountId', None),
        ('ai.user.id', None),
        ('ai.user.authUserId', None)
    ])
    
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self._values = {
        }
        self._initialize()
        
    @property
    def account_id(self):
        """The account_id property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.user.accountId' in self._values:
            return self._values['ai.user.accountId']
        return self._defaults['ai.user.accountId']
        
    @account_id.setter
    def account_id(self, value):
        """The account_id property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.user.accountId'] and 'ai.user.accountId' in self._values:
            del self._values['ai.user.accountId']
        else:
            self._values['ai.user.accountId'] = value
        
    @property
    def id(self):
        """The id property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.user.id' in self._values:
            return self._values['ai.user.id']
        return self._defaults['ai.user.id']
        
    @id.setter
    def id(self, value):
        """The id property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.user.id'] and 'ai.user.id' in self._values:
            del self._values['ai.user.id']
        else:
            self._values['ai.user.id'] = value
        
    @property
    def auth_user_id(self):
        """The auth_user_id property.
        
        Returns:
            (string). the property value. (defaults to: None)
        """
        if 'ai.user.authUserId' in self._values:
            return self._values['ai.user.authUserId']
        return self._defaults['ai.user.authUserId']
        
    @auth_user_id.setter
    def auth_user_id(self, value):
        """The auth_user_id property.
        
        Args:
            value (string). the property value.
        """
        if value == self._defaults['ai.user.authUserId'] and 'ai.user.authUserId' in self._values:
            del self._values['ai.user.authUserId']
        else:
            self._values['ai.user.authUserId'] = value
        
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

