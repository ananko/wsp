from client import ServerProxy


if __name__ == '__main__':
    server = ServerProxy('http://localhost:8001')
    description = server.get_description()
    print(description)
    service = server.get_service('resource_monitor')
    print(service.description)
    print(service.get_info())
