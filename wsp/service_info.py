from server import SimpleWSPService
from server import SimpleWSPServer


class InformationService(SimpleWSPService):
    def __init__(self):
        name = 'information_service'
        description = 'Information service'
        SimpleWSPService.__init__(self, name, description)
        self.add_method(self.register)
        self.add_method(self.deregister)
        self.add_method(self.get_info)
        self.registry = {}

    def register(self, data: dict) -> None:
        self.registry[data['network_name']] = data

    def deregister(self, data: dict) -> None:
        if data['network_name'] in self.registry:
            self.registry.pop(data['network_name'], None)

    def get_info(self, data: dict) -> dict:
        return self.registry


if __name__ == '__main__':
    info_service = InformationService()

    PORT = 8002
    server = SimpleWSPServer(('', PORT))
    server.register(info_service)

    try:
        print('Starting WSP server at port %d' % PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting')
        server.server_close()
