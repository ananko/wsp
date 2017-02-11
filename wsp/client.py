import urllib
import http.client
from http import HTTPStatus
import yaml

from server import WSP_VERSION


class Transport:
    user_agent = 'python/wsp'

    def __init__(self):
        self._connection = (None, None)
        self._extra_headers = []

    def request(self, host, path, request_type='POST',
                request_body='', verbose=False):
        connection = self.make_connection(host)
        headers = self._extra_headers[:]
        if verbose:
            connection.set_debuglevel(1)
        connection.putrequest(request_type, path)
        headers.append(('content-type', 'text/plain'))
        headers.append(('user-agent', self.user_agent))
        self.send_headers(connection, headers)
        self.send_content(connection, request_body)

        resp = connection.getresponse()
        if resp.status != HTTPStatus.OK:
            print('WTF')
            return None
        return resp.read()

    def make_connection(self, host):
        if self._connection and host == self._connection[0]:
            return self._connection[1]
        chost, self._extra_headers, x509 = self.get_host_info(host)
        self._connection = host, http.client.HTTPConnection(chost)
        return self._connection[1]

    def get_host_info(self, host):
        extra_headers = []
        auth, host = urllib.parse.splituser(host)
        x509 = {}
        if auth:
            raise NotImplemented

        return host, extra_headers, x509

    def close(self):
        host, connection = self._connection
        if connection:
            self._connection = (None, None)
            connection.close()

    def send_headers(self, connection, headers):
        for key, value in headers:
            connection.putheader(key, value)

    def send_content(self, connection, request_body):
        connection.putheader('content-length', str(len(request_body)))
        connection.endheaders(request_body)


RETURN_TYPES = {
    'int': int,
    'dict': dict,
}


class _Method:
    def __init__(self, service, name, description):
        self.service = service
        self.name = name
        self.description = description
        self._args = {}
        self._kwargs = {}
        self._return_type = RETURN_TYPES[
            self.description['return_info']['type']
        ]
        for arg_name in self.description['params']:
            arg = self.description['params'][arg_name]
            arg['name'] = arg_name
            self._args[arg['order']] = arg
            self._kwargs[arg_name] = arg

    def __call__(self, *args, **kwargs):
        request = {
            'type': 'wsp/request',
            'version': WSP_VERSION,
            'service': self.service.name,
            'method': self.name,
        }
        req_args = {}
        for i, arg in enumerate(args):
            req_args[self._args[i]['name']] = arg
        for key, value in kwargs:
            req_args[key] = value
        request['args'] = req_args
        response = self.service._handle_request(request)
        result = self._return_type(response['result'])
        return result


class ServiceProxy:
    def __init__(self, server, name, description):
        self.server = server
        self.name = name
        self.description = description
        self._methods = {}
        for name, method in self.description['methods'].items():
            m = _Method(self, name, method)
            self._methods[name] = m
            self.__setattr__(name, m)

    def _handle_request(self, request):
        return self.server._handle_request(request)


class ServerProxy:
    def __init__(self, uri, transport=None, encoding='utf-8', verbose=False):
        type, uri = urllib.parse.splittype(uri)
        if type not in ('http', 'https'):
            raise Exception("Protocol '%s' is not supported" % type)
        self.__host, self.__handler = urllib.parse.splithost(uri)
        self.__encoding = encoding
        self.__verbose = verbose

        if not transport:
            if type == 'http':
                handler = Transport
                extra_kwargs = {}
            else:
                raise NotImplemented
            transport = handler(**extra_kwargs)
        self.__transport = transport

    def get_description(self):
        response = self.__transport.request(self.__host,
                                            '/', 'GET').decode(self.__encoding)
        response = yaml.load(response)

        return response

    def get_service(self, name):
        description = self.get_description()
        if name not in description['services']:
            raise Exception(
                "Service '%s' is not provided by the server" % name)

        description = self.__transport.request(
            self.__host, '/%s' % name, 'GET').decode(self.__encoding)
        description = yaml.load(description)
        service = ServiceProxy(self, name, description)
        return service

    def _handle_request(self, request):
        response = self.__transport.request(
            self.__host, '/%s' % request['service'],
            'POST', yaml.dump(request).encode(
                self.__encoding)).decode(self.__encoding)
        response = yaml.load(response)
        return response
