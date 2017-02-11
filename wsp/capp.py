from client import ServerProxy


if __name__ == '__main__':
    server = ServerProxy('http://localhost:8001')
    description = server.get_description()
    print(description)
    service = server.get_service('nm')
    print(service.description)
    print(service.get_info())
    print(service.get_status())
    service.start_job()
    while True:
        status = service.get_status()
        print(status)
        if status['state'] == 'idle':
            break
    # print(service.add(2, 4))
    # print(service.add(6, 43243))
    # print(service.sub(6, 9))
    # print(service.sub(123421, 3234))
