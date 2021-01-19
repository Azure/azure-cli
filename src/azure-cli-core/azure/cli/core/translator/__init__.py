import inspect


class ClientFactory:

    def __init__(self, client_factory_func):
        self.module_name = inspect.getmodule(client_factory_func).__name__
        self.name = client_factory_func.__name__
        self.client_factory_func = client_factory_func

    def __call__(self, *args, **kwargs):
        return self.client_factory_func(*args, **kwargs)

    def __str__(self):
        return "{}#{}".format(self.module_name, self.name)


def client_factory_register(client_factory):
    return ClientFactory(client_factory)
