import random

description_server = {
    'type': 'yamlwsp/description',
    'version': '0.1',
    'url': 'TBD',
    'services': ['calculator', 'iamlucky']
}

description_service_calculator = {
    'type': 'yamlwsp/description',
    'version': '0.1',
    'url': 'TBD',
    'servicename': 'calculator',
    'types': {},
    'methods': {
        'add': {
            'doc_lines': 'Adds two numbers',
            'params': {
                'a': {
                    'doc_lines': 'fist argument',
                    'def_order': '0',
                    'type': float.__name__,
                    'optional': False,
                },
                'b': {
                    'doc_lines': 'second argument',
                    'def_order': '1',
                    'type': float.__name__,
                    'optional': False,
                }
            },
            'ret_info': {
                'doc_lines': 'Sum of aguments',
                'type': float.__name__,
            }
        },
        'sub': {
            'doc_lines': 'Substitutes two numbers',
            'params': {
                'a': {
                    'doc_lines': 'fist argument',
                    'def_order': '0',
                    'type': float.__name__,
                    'optional': False,
                },
                'b': {
                    'doc_lines': 'second argument',
                    'def_order': '1',
                    'type': float.__name__,
                    'optional': False,
                }
            },
            'ret_info': {
                'doc_lines': 'Difference of aguments',
                'type': float.__name__,
            }
        },
    },
}

request = {
    'type': 'yamlwsp/request',
    'version': '0.1',
    'url': 'TBD',
    'servicename': 'calculator',
    'methodname': 'add',
    'args': {
        'a': '2',
        'b': '3',
    },
    'mirror': '1',
}

response = {
    'type': 'yamlwsp/response',
    'version': '0.1',
    'url': 'TBD',
    'servicename': 'calculator',
    'methodname': 'add',
    'result': '5',
    'mirror': '1',
}

fault = {
    'type': 'yamlwsp/fault',
    'version': '0.1',
    'url': 'TBD',
    'fault': {
        'code': 'server',
        'string': 'OMG',
    }
}


TYPES = {
    'float': float
}


class Method():
    def __init__(self, name, description, service):
        self.name = name
        self.description = description
        self.service = service
        self.__doc__ = self.description['doc_lines']
        self.args = self.description['params']
        for arg in self.args:
            self.args[arg]['def_order'] = int(self.args[arg]['def_order'])
            self.args[arg]['type'] = TYPES[self.args[arg]['type']]
        self.return_info = self.description['ret_info']
        self.return_info['type'] = TYPES[self.return_info['type']]

    def __call__(self, *args, **kwargs):
        if len(self.args) != (len(args) + len(kwargs)):
            raise Exception('WFT')
        mirror = random.randint(1, 100)
        mirror = 1
        params = {}
        for i, arg in enumerate(args):
            for param in self.args:
                if self.args[param]['def_order'] == i:
                    params[param] = arg
                    break
        for key, value in kwargs.items():
            param[key] = value

        request = {
            'type': 'yamlwsp/request',
            'version': '0.1',
            'url': 'TBD',
            'servicename': self.service.name,
            'methodname': self.name,
            'args': params,
            'mirror': mirror,
        }
        response = self.service.process(request)
        assert mirror == int(response['mirror']), 'wrong mirror value'
        assert self.service.name == response['servicename'], 'Wrong \
service name'
        assert self.name == response['methodname'], 'Wrong method name'
        result = self.return_info['type'](response['result'])

        return result


class Service():
    def __init__(self, name, description, proxy):
        self.name = name
        self.proxy = proxy
        self.description = description
        self.methods = {}
        for method, method_description in self.description['methods'].items():
            self.methods[method] = Method(method, method_description, self)
            self.__setattr__(method, self.methods[method])

    def process(self, request):
        print(request)
        return response


class ProxyServer():
    def __init__(self):
        self.description = description_server
        self.services = {}

    def get_services(self):
        return self.description['services']

    def get_service(self, name):
        if name in self.services:
            return self.services[name]

        service = Service(name, description_service_calculator, self)
        self.services[name] = service
        return service


class Server():
    def __init__(self):
        self.description = 'Simple YAML WSP Server'
