import yaml
from wsgiref.util import request_uri
from urllib.parse import urlparse


routes = {}


primitive_types = ['str', 'int', 'float']


class Service():
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri
        self._types = {}
        self._methods = {}

        routes[uri] = self

    def get_description(self):
        description = {}
        description['type'] = 'yamlwsp/description'
        description['version'] = '1.0'
        description['servicename'] = self.name
        description['url'] = self.uri
        description['types'] = {}
        description['methods'] = {}
        for method in self._methods:
            description['methods'][method] = {
                'doc_lines': self._methods[method]['doc_lines'],
                'params': self._methods[method]['params'],
                'ret_info': self._methods[method]['ret_info']
            }

        return description

    def register_method(self, function, args, return_type):
        name = function.__name__
        params = {}
        for i, arg in enumerate(args):
            params[arg] = {'type': args[arg].__name__, 'def_order': i + 1}
        m = {'function': function,
             'doc_lines': function.__doc__,
             'params': params,
             'ret_info': {'type': return_type.__name__}}
        self._methods[name] = m

        if return_type.__name__ not in primitive_types:
            raise NotImplementedError(
                "Type '%s' is not supported yet" % return_type.__name__)

        for arg in args:
            if args[arg].__name__ not in primitive_types:
                raise NotImplementedError(
                    "Type '%s' is not supported yet" % args[arg].__name__)


def get_service(path):
    path = path.rsplit('/', 1)[0]
    if path in routes:
        return routes[path]
    else:
        raise Exception("Path '%s' is not found" % (path))


def handle_request(environ, start_response):
    content_length = environ.get('CONTENT_LENGTH', 0)
    if content_length == '':
        request_body_size = 0
    else:
        request_body_size = int(content_length)
    request_body = environ['wsgi.input'].read(request_body_size)
    uri = request_uri(environ)
    url = urlparse(uri)
    if environ['REQUEST_METHOD'] == 'GET':
        return handle_get_request(start_response, url, request_body)
    elif environ['REQUEST_METHOD'] == 'POST':
        return handle_post_request(start_response, url, request_body)
    else:
        raise Exception(
            'Unsupported request method: %s' % (environ['REQUEST_METHOD']))


def handle_get_request(start_response, url, request_body):
    service = get_service(url.path)
    description = service.get_description()
    if url.path.endswith('description'):
        content_type = 'application/yaml'
        body = yaml.dump(description)
    else:
        content_type = 'text/html'
        body = get_body_html(description)
    return send_response(start_response, content_type,
                         body.encode('utf-8'), '200 OK')


def get_body_html(description):
    html = []
    html.append('<h1>%s</h1>' % description['servicename'])
    html.append('<h2>Types:</h2>')
    html.append('<h2>Methods:</h2>')
    html.append(
        '<p>JAML Web Service version %s</p>' % description['version'])
    return ('\n'.join(html))


def send_response(start_response, content_type, body, status):
    headers = [('Content-Type', content_type),
               ('Content-Length', str(len(body)))]
    headers = [('Content-Type', content_type)]
    start_response(status, headers)
    return [body]


def application(environ, start_response):
    return handle_request(environ, start_response)
