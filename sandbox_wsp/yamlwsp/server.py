import yaml
from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer
from errors import Fault


class SimpleYAMLWSPDispatcher:

    def __init__(self, encoding=None):
        self.funcs = {}
        self.services = {}
        self.encoding = encoding or 'utf-8'

    def register_service_method(self, service, function, name=None,
                                args=None, return_info=None, docs=None):
        if service not in self.services:
            self.services[service] = {}
        if not name:
            name = function.__name__
        self.services[service][name] = {'function': function,
                                        'args': args,
                                        'return_info': return_info,
                                        'docs': docs,
                                        }

    def generate_description(self, path=None):
        desc = {}
        desc['type'] = 'yamlwsp/description'
        desc['version'] = '1.0'
        desc['url'] = 'TBD'
        service = path.split('/')[1]
        if service in self.services:
            service = self.services[service]
            desc['types'] = {}
            desc['methods'] = {}
            for name in service:
                method = service[name]
                method_desc = {}
                method_desc['doc_line'] = method['docs']
                method_desc['params'] = {}
                for i, arg in enumerate(method['args']):
                    mdesc = method['args'][arg]
                    mdesc['def_order'] = i + 1
                    mdesc['type'] = mdesc['type'].__name__
                    method_desc['params'][arg] = mdesc

                method_desc['ret_info'] = method['return_info']
                method_desc['ret_info']['type'] = \
                    method_desc['ret_info']['type'].__name__

                desc['methods'][name] = method_desc
        elif service == '':
            desc['services'] = []
            for service in self.services:
                desc['services'].append(service)
        else:
            desc = {
                'type': 'yamlwsp/fault',
                'version': '1.0',
                'fault': 'client',
                'string': "Service '%s' is not registered" % service
            }
        return yaml.dump(desc).encode(self.encoding)

    def _marshaled_dispatch(self, data, path=None):
        # import pdb; pdb.set_trace()
        data = yaml.load(data)
        try:
            service_name = path.split('/')[1]
            service = self.services[service_name]
            method = service[data['methodname']]
            f = method['function']
            args = data['args']
            value_args = {}
            for arg in method['args']:
                arg_name = arg
                arg_value = method['args'][arg]['type'](args[arg])
                value_args[arg_name] = arg_value
            res = f(*value_args.values())
            resp = {
                'type': 'yaml/response',
                'version': '1.0',
                'servicename': service_name,
                'method_name': data['methodname'],
                'result': str(res)
            }
            response = resp
        except KeyError:
            raise Exception('Service "%s" is not registered' % service_name)

        return yaml.dump(response).encode(self.encoding)


class SimpleYAMLWSPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            response = self.server.generate_description(self.path)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-length', '0')
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/yaml')
            self.send_header('Content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def do_POST(self):
        try:
            data_size = int(self.headers['content-length'])
            data = self.rfile.read(data_size)
            if data is None:
                return  # response has been sent
            response = self.server._marshaled_dispatch(data, self.path)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-length', '0')
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/yaml')
            self.send_header('Content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def log_request(self, code='-', size='-'):
        if self.server.logRequests:
            BaseHTTPRequestHandler.log_request(self, code, size)


class SimpleYAMLWSPServer(TCPServer,
                          SimpleYAMLWSPDispatcher):
    '''Simple YAML-WSP server'''
    allow_reuse_address = True

    # Warning: this is for debugging purposes only! Never set this to True in
    # production code, as will be sending out sensitive information (exception
    # and stack trace details) when exceptions are raised inside
    # SimpleXMLRPCRequestHandler.do_POST
    _send_reuse_address = True  # TODO: change to False

    def __init__(self, addr, requestHandler=SimpleYAMLWSPRequestHandler,
                 logRequests=True, encoding=None, bind_and_activate=True):
        self.logRequests = logRequests
        SimpleYAMLWSPDispatcher.__init__(self, encoding)
        TCPServer.__init__(self, addr, requestHandler, bind_and_activate)


if __name__ == '__main__':
    PORT = 8001
    server = SimpleYAMLWSPServer(('', PORT))
    server.register_service_method('calculator', pow,
                                   args={'a': {'type': float,
                                               'doc_lines': None,
                                               'optional': False},
                                         'b': {'type': float,
                                               'doc_lines': None,
                                               'optional': False}},
                                   return_info={'type': float,
                                                'doc_lines': None},
                                   docs='Equivalent to x**x')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Keyboard interrupt recieved, exiting')
        server.server_close()
