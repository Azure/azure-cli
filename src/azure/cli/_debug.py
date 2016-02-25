import os  
  
def allow_debug_connection(client):  
    if should_allow_debug_connection():  
        client.config.connection.verify = False  
  
def should_allow_debug_connection():  
    try:  
        return bool(os.environ['AllowDebug'])  
    except KeyError:   
        return False  
