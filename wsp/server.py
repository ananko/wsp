class Service():
    def __init__(self, name, description=None):
        self.name = name
        self.description = None
        self.methods = {}

    def add_method(self, function, name=None):
        if not name:
            name = function.__name__
        if name in self.methods:
            raise Exception("Method '%s' is already registered" % name)
        self.methods[name] = function
        self.__setattr__(name, self.methods[name])


class Server():
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.services = {}

    def add_service(self, service):
        if service.name in self.services:
            raise Exception("Service '%' is already registered" % service.name)
        self.services[service.name] = service

    def get_description(self):
        return self.description

    def get_services(self):
        return self.services.keys()

    def get_service(self, name):
        if name not in self.services:
            raise Exception("Service '%s' is not registered" % name)
        return self.services[name]
