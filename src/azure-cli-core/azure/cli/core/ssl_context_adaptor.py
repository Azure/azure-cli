import requests.adapters
import ssl
import truststore

class SSLContextAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        kwargs['ssl_context'] = ctx
        return super(SSLContextAdapter, self).init_poolmanager(*args, **kwargs)
