from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer
import yaml
import inspect


WSP_VERSION = 0.1


class SimpleWSPService:

    class Method:
        def __init__(self, function):
            self.function = function
            self.name = self.function.__name__
            self.signature = inspect.signature(function)

        def __call__(self, *args, **kwargs):
            # should I use signature.bind?
            return self.function(*args, **kwargs)

        def get_return_info(self):
            return self.signature.return_annotation

        def get_params(self):
            params = []
            for name, param in self.signature.parameters.items():
                params.append((name, param.annotation))
            return params

    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.methods = {}

    def add_method(self, function):
        method = SimpleWSPService.Method(function)
        for name, param in method.signature.parameters.items():
            if param.annotation == param.empty:
                raise Exception("Type of parameter '%s' is not specified"
                                % name)
        if method.signature.return_annotation == method.signature.empty:
            raise Exception('Return type is not specifed')
        self.methods[method.name] = method
        name = method.name
        if hasattr(self, name):
            name = '___' + name
        self.__setattr__(name, method)

    def get_method(self, name):
        if name not in self.methods:
            raise Exception("Method '%s' is not registered" % name)
        return self.methods[name]


class SimpleWSPDispatcher:
    def __init__(self, encoding=None):
        self.encoding = encoding or 'utf-8'
        self.services = {}

    def register(self, service):
        if service.name in self.services:
            raise Exception("Service '%s' is already registered"
                            % service.name)
        self.services[service.name] = service

    def generate_description(self, path):
        desc = {
            'type': 'wsp/description',
            'version': WSP_VERSION,
            'url': '%s' % path
        }
        service = path.split('/')[1]
        if service is '':
            desc['services'] = list(self.services.keys())
        elif service in self.services:
            service = self.services[service]
            desc['service'] = service.name
            desc['description'] = service.description
            desc['types'] = {}
            desc['methods'] = {}
            for method in service.methods.values():
                mdesc = {}
                mdesc['params'] = {}
                params = method.get_params()
                for i, (name, ptype) in enumerate(params):
                    pdesc = {}
                    pdesc['type'] = ptype.__name__
                    pdesc['order'] = i
                    mdesc['params'][name] = pdesc
                return_type = method.get_return_info()
                mdesc['return_info'] = {
                    'type': None if not return_type else return_type.__name__
                }
                desc['methods'][method.name] = mdesc
        else:
            desc['type'] = 'wsp/fault'
            fault = {
                'code': 'client',
                'description': "Service '%s' is not registered" % service
            }
            desc['fault'] = fault

        return yaml.dump(desc).encode(self.encoding)

    def dispatch(self, path, data):
        service = path.split('/')[1]
        if service in self.services:
            resp = {
                'type': 'wsp/response',
                'version': WSP_VERSION,
                'url': path
            }
            request = yaml.load(data.decode(self.encoding))
            if request['service'] != service:
                raise Exception("Requested service '%s' instead of '%s'"
                                % (request['service'], service))
            service = self.services[service]
            resp['method'] = request['method']
            method = service.get_method(request['method'])
            req_args = request['args']
            params = method.get_params()
            args = {}
            for i, (name, ptype) in enumerate(params):
                if name not in req_args:
                    raise Exception("Wrong argument '%s'" % name)
                args[name] = ptype(req_args[name])  # add try for conversion
            result = method(**args)
            resp['result'] = result
            if 'mirror' in request:
                resp['reflection'] = request['mirror']
        else:
            resp['type'] = 'wsp/fault'
            fault = {
                'code': 'client',
                'description': "Service '%s' is not registered" % service
            }
            resp['fault'] = fault

        return yaml.dump(resp).encode(self.encoding)


class SimpleWSPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            response = self.server.generate_description(self.path)
        except Exception:
            # TODO: change it to send_error
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_header('Content-length', '0')
            self.end_headers()
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header('content-type', 'text/plain')
            self.send_header('content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def do_POST(self):
        try:
            data_size = int(self.headers['content-length'])
            data = self.rfile.read(data_size)
            if data is None:
                return  # response has been sent
            response = self.server.dispatch(self.path, data)
        except Exception:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_header('Content-length', '0')
            self.end_headers()
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header('content-type', 'text/plain')
            self.send_header('content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def log_request(self, code='-', size='-'):
        if self.server.logRequests:
            BaseHTTPRequestHandler.log_request(self, code, size)


class SimpleWSPServer(TCPServer, SimpleWSPDispatcher):
    allow_reuse_address = True

    def __init__(self, addr, requestHandler=SimpleWSPRequestHandler,
                 logRequests=True, encoding=None, bind_and_activate=True):
        self.logRequests = logRequests
        SimpleWSPDispatcher.__init__(self, encoding)
        TCPServer.__init__(self, addr, requestHandler, bind_and_activate)


if __name__ == '__main__':
    PORT = 8001
    server = SimpleWSPServer(('', PORT))

    service = SimpleWSPService('calc')

    def add(a: int, b: int) -> int:
        return a + b
    service.add_method(add)

    def sub(a: int, b: int) -> int:
        return a - b
    service.add_method(sub)

    server.register(service)

    try:
        print('Starting WSP server at port %d' % PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting')
        server.server_close()
