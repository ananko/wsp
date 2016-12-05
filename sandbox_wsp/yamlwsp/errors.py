class Error(Exception):
    pass


class Fault(Error):
    '''Indicates an YAMLWSP fault package.'''

    def __init__(self, faultCode, faultString, **extra):
        Error.__init__(self)
        self.faultCode = faultCode
        self.faultString = faultString

    def __repr__(self):
        return "<%s %s: %r>" % (self.__class__.__name__,
                                self.faultCode, self.faultString)
