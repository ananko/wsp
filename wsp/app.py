from server import SimpleWSPService
from server import SimpleWSPServer
from client import ServerProxy
import time
import threading
import platform
import socket


def worker(service):
    time.sleep(10)
    service._state = 'idle'


class NMService(SimpleWSPService):
    def __init__(self, config):
        self.config = config
        name = 'nm'
        description = 'NodeManager is responsible for managing node'
        SimpleWSPService.__init__(self, name, description)
        self.add_method(self.get_info)
        self.add_method(self.get_status)
        self.add_method(self.start_job)
        self._state = 'idle'
        self.info_server = ServerProxy(self.config['info_service_address'])
        self.info_service = self.info_server.get_service('information_service')
        self.info_service.register(
            {
                'network_name': socket.gethostbyaddr(socket.gethostname())[1],
                'architecture': platform.architecture()[0],
                'ip_address': socket.gethostbyaddr(socket.gethostname())[-1],
                'admin': 'admin@example.com',
                'os': platform.system(),
                'software': [],
                'features': [],
            }
        )

    def get_info(self) -> dict:
        return {
            'node': {
                'host': {
                    'OS': 'Windows',
                    'version': '8',
                },
                'jobs': {
                    'run_cmd': {
                        'args': {
                            'path': {'type': str.__name__},
                            'cmd_line': {'type': str.__name__},
                        },
                        'return_info': {
                            'output': {'type': str.__name__},
                            'errors': {'type': str.__name__},
                            'files': [],
                        }
                    }
                }
            }
        }

    def get_status(self) -> dict:
        return {
            'state': self._state
        }

    def start_job(self) -> dict:
        self._state = 'running'
        t = threading.Thread(target=worker, args=(self, ))
        t.start()
        return {
            'state': self._state
        }


if __name__ == '__main__':
    config = {
        'info_service_address': 'http://localhost:8001',
    }
    nm_service = NMService(config)

    PORT = 8001
    server = SimpleWSPServer(('', PORT))

    server.register(nm_service)

    try:
        print('Starting WSP server at port %d' % PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting')
        server.server_close()
