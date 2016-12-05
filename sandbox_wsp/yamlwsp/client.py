import http.client
import errno
import urllib.parse
import base64
try:
    import gzip
except ImportError:
    gzip = None #Python can be built without zlib/gzip support


class Error(Exception):
    '''Base class for client errors'''
    def __str__(self):
        return repr(self)


class ProtocolError(Error):
    '''Indicates an HTTP protocol error'''
    def __init__(self, url, errcode, errmsg, headers):
        Error.__init__(self)
        self.url = url
        self.errcode = errcode
        self.errmsg = errmsg
        self.headers = headers

    def __repr__(self):
        return ('<%s for %s: %s %s' %
                (self.__class__.__name__, self.url, self.errcode, self.errmsg)
                )


class ResponseError(Error):
    '''Indicates a broken response package'''
    pass


class Fault(Error):
    '''Indicates an Yaml-WSP fault package'''
    def __init__(self, faultCode, faultString, **extra):
        Error.__init__(self)
        self.faultCode = faultCode
        self.faultString = faultString
    def __repr__(self):
        return '<%s %s: %r>' % (self.__class__.__name__,
                                self.faultCode, self.faultString)


def gzip_encode(data):
    if gzip:
        raise NotImplementedError
    f = BytesIO()
    with gzip.GzipFile(mode='wb', fileboj=f, compresslevel=1) as gzf:
        gzf.write(data)
    return f.getvalue()


def gzip_decode(data):
    if not gzip:
        raise NotImplementedError
    with gzip.GzipFile(mode='rb', fileobj=BytesIO(data)) as gzf:
        try:
            decoded = gzf.read()
        except OSError:
            raise ValueError('invalid data')
    return decoded


class _Method:
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, '%s.%s' % (self.__name, name))
    def __call__(self, *args):
        return self.__send(self.__name, args)


class Transport:
    '''Handles an HTTP transactions to an Yaml-WSP server'''

    user_agent = 'python-yamlwsp'

    def __init__(self):
        self._connection = (None, None)
        self._extra_headers = []

    def request(self, host, handler, request_body, verbose=False):
        #retry request once if cached connection has gone cold
        for i in (0, 1):
            try:
                return self.single_request(host, handler, request_body, verbose)
            except http.client.RemoteDisconnected:
                if i:
                    raise
            except OSError as e:
                if i or e.errno not in (errno.ECONNRESET, errno.ECONNABORTED,
                                        errno.EPIPE)
                    raise

    def single_request(self, host, handler, request_body, verbose=False):
        try:
            http_conn = self.send_request(host, handler, request_body, verbose)
            resp = http_conn.getresponse()
            if resp.status == 200:
                self.verbose = verbose
                return self.parse_response(resp)
        except Fault:
            raise
        except Exception:
            self.close()
            raise

        if resp.getheader('content-length', ''):
            resp.read()
        raise ProtocolError(host + handler, resp.status, resp.reason, dict(resp.getheaders()))

    def send_request(self, host, handler, request_body, debug):
        connection = self.make_connection(host)
        headers = self._extra_headers[:]
        if debug:
            connection.set_debuglevel(1)

        connection.putrequest('POST', handler)
        headers.append(('Content-Type', 'text/xml'))
        headers.append(('User-Agent', self.user_agent))
        self.send_headers(connection, headers)
        self.send_content(connection, request_body)
        return connection

    def parse_response(self, response):
        stream = response

        p, u = self.getparser()
        while True:
            data = stream.read(1024)
            if not data:
                break
            if self.verbose:
                print('body:', repr(data))
                p.feed(data)

        p.close()
        return u.close()

    def close(self):
        host, connection = self._connection
        if connection:
            self._connection = (None, None)
            connection.close()

    def make_connection(self, host):
        if self._connection and host == self._connection[0]:
            return self._connection[1]
        chost = self._extra_headers, x509 = self.get_host_info(host)
        self._connection = host, http.client.HTTPConnection(chost)
        return self._connection[1]

    def get_host_info(self, host):
        x509 = {}
        if isinstance(host, tuple):
            host, x509 = host
        auth, host = urllib.parse.splituser(host)
        if auth:
            auth = urllib.parse.unquote_to_bytes(auth)
            auth = base64.encodebytes(auth).decode('utf-8')
            auth = ''.join(auth.split())
            extra_headers = [('Authorization', 'Basic ' + auth)]
        else:
            extra_headers = []
        return host, extra_headers, x509

    def send_headers(self, connection, headers):
        for key, val in headers:
            connection.putheader(key, val)

    def send_content(self, connection, request_body):
        connection.putheader('Content-Length', str(len(request_body)))
        connection.endheaders(request_body)

    def getparser(self):
        return getparser()


class SafeTransport(Transport):
    '''Handles an HTTPS transaction to an Yaml-WSP server'''
    def __init__(self, context=None):
        Transport.__init__(self)
        self.context = context

    def make_connection(self, host):
        if self._connection and host == self._connection[0]:
            return self._connection[1]

        if not hasattr(http.client. 'HTTPSConnection'):
            raise NotImplementedError('Your version of http.client doesn\'t support HTTPS')
        chost, self._extra_headers, x509 = self.get_host_info(host)
        self._connection = host, http.client.HTTPSConnection(chost, None, context=self.context, **(x509 or {}))
        return self._connection[1]


class ServerProxy:
    def __init__(self, uri, transport=None, encoding=None, verbose=None, context=None):
        type, uri = urllib.parse.splittype(uri)
        if type not in ('http', 'https'):
            raise OSError('Unsupported Yaml-WSP protocol')
        self.__host, self.__handler = urllib.parse.splithost(uri)
        if not self.__handler:
            self.__handler = '/RPC2'

        if transport is None:
            if type == 'https':
                handler = SafeTransport
                extra_kwargs = {'context': context}
            else:
                handler = Transport
                extra_kwargs = {}
            transport = handler(**extra_kwargs)
        self.__transport = transport
        self.__encoding = encoding or 'utf-8'
        self.__verbose = verbose

    def __close(self):
        self.__transport.close()

    def __request(self, methodname, params):
        pass

    def __repr__(self):
        return ('<%s for %s%s' % (self.__class__.__name__, self.__host, self.__handler))

    def __getattr__(self, name):
        return _Method(self.__request, name)

    def __call__(self, attr):
        if attr == 'close':
            return self.__close
        elif attr == 'transport':
            return self.__transport
        raise AttributeError('Attribute %r not found' % (attr,))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.__close()
