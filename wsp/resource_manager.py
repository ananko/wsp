from server import SimpleWSPServer
from server import SimpleWSPService

class RMService(SimpleWSPService):
    def __init__(self, config):
        self.config = config
        name = 'rm'
        description = 'Resource Manager is responsible for resource management'
        SimpleWSPService.__init__(self, name, description)
