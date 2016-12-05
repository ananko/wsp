from yamlwsp.client import ServiceConnection


connection = ServiceConnection('localhost', 8051, '/calculator')
calculator = connection.get_service()
print(calculator.description)
