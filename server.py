from wsgiref.simple_server import make_server
from yamlwsp.server import Service, application


port = 8051

service = Service('Calculator', '/calculator')


def add(a, b):
    return a + b


service.register_method(function=add,
                        args={'a': float, 'b': float},
                        return_type=float)

httpd = make_server('', port, application)
print('Serving on port %d...' % port)
httpd.serve_forever()
