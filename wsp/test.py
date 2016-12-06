class Map(dict):
    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]


class YService():
    def __init__(self):
        pass


class YServer():
    def __init__(self):
        self.description = Map(type='yamlwsp/description',
                               version='0.1',
                               url='TBD',
                               services=['calculator', 'iamlucky'],)
        self.services = {}

    def add_service(self, service):
        self.services[service.name] = service

    def get_services(self):
        return self.description.services

    def get_service(self, name):
        if name not in self.services:
            raise Exception("Service '%s' is not registered" % name)
        return self.services[name]


class Service():
    def __init__(self, description):
        self.description = Map(description)


class ProxyServer():
    def __init__(self, server):
        self.server = server

    def get_services(self):
        return self.server.get_services()

    def get_service(self, name):
        services = self.server.get_services()
        if name not in services:
            raise Exception("Service '%s' is not provide by the server" % name)

        service_description = self.server.get_service(name)
        service = Service(service_description)
        self.services[name] = service
        return service
