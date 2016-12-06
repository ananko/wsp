# TODO: consider caching


class Service():
    def __init__(self, name, proxy):
        self.name = name
        self.proxy = proxy
        self.impl = self.proxy.server.get_service(self.name)
        for name, functions in self.impl.methods.items():
            self.__setattr__(name, functions)


class ProxyServer():
    def __init__(self, server):
        self.server = server
        self.description = self.server.get_description()

    def get_services(self):
        return self.server.get_services()

    def get_service(self, name):
        services = self.get_services()
        if name not in services:
            raise Exception("Service '%s' is not registered" % name)

        service = Service(name, self)

        return service
