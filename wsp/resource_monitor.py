from server import SimpleWSPServer
from server import SimpleWSPService


class ServiceResourceMonitor(SimpleWSPService):
    def __init__(self, config):
        self.config = config
        name = 'resource_monitor'
        description = 'Resource Monitor is responsible for resource monitoring'
        SimpleWSPService.__init__(self, name, description)
        self.add_method(self.register)
        self.add_method(self.get_info)
        self.registry = {}

    def register(self, data: dict) -> None:
        self.registry[data['network_name']] = data

    def get_info(self) -> dict:
        return self.registry


if __name__ == '__main__':
    config = {
        'info_service_address': 'http://localhost:8001',
    }
    service_rm = ServiceResourceMonitor(config)

    PORT = 8001
    server = SimpleWSPServer(('', PORT))
    server.register(service_rm)

    try:
        print('Starting WSP server at port %d' % PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting')
        server.server_close()
