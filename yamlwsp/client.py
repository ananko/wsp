import yaml
from http.client import HTTPConnection


class Service():
    def __init__(self, service_connection):
        self.description = None
        self._service_connection = service_connection
        self._service_connection.connection.request(
            'GET', '%s/%s' % (self._service_connection.path, 'description'))
        response = self._service_connection.connection.getresponse()
        if response.status == 200:
            description = response.read()
            self.description = yaml.load(description.decode())
        else:
            raise Exception('Cannot get service description')

        methods = self.description['methods']

        class Method():
            def __init__(self, name, service):
                self.name = name
                self._service = service
                methods = self._service.description['methods']
                self.params = methods[self.name]['params']

            def __call__(self, *args, **kwargs):
                request_args = {}
                for i, value in enumerate(args):
                    key = self._get_param_by_index(i)
                    request_args[key] = value
                for key, value in kwargs.items():
                    request_args[key] = value
                request = {}
                request['type'] = 'jamlwsp/request'
                request['version'] = '1.0'
                request['methodname'] = self.name
                request['args'] = request_args

                connection = self._service._serivice_connection.connection
                connection.send_request(request)
                return response['result']

            def _get_param_by_index(self, index):
                for key in self.params:
                    if (int(self.params[key]['def_order'])) == index:
                        return key
                return None

        for name in methods:
            self.__dict__[name] = Method(name,
                                         self._service_connection.connection)


class ServiceConnection():
    def __init__(self, host, port, path, encription='utf-8'):
        self.host = host
        self.port = port
        self.path = path
        self.encription = encription
        self.connection = HTTPConnection(self.host, self.port)

    def get_service(self):
        return Service(self)

    def send_request(self, request):
        request = request.encode('utf-8')
        request_len = len(request)
        header = {'Content-Type': 'application/json',
                  'Content-Length': request_len}
        self.connection.request('POST', self.path, request, header)
        response = self.connection.getresponse()
        data = response.read()
        return yaml.load(data.encode('utf-8'))
