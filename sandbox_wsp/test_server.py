import sys
from xmlrpc.server import DocXMLRPCServer

if __name__ == '__main__':
    import datetime

    class ExampleService:
        def getData(self):
            return '42'

        class currentTime:
            @staticmethod
            def getCurrentTime():
                return datetime.datetime.now()

    server = DocXMLRPCServer(("localhost", 8002))
    server.register_function(pow)
    server.register_function(lambda x, y: x + y, 'add')
    server.register_instance(ExampleService(), allow_dotted_names=True)
    server.register_multicall_functions()
    print('Serving XML-RPC on localhost port 8000')
    print('It is advisable to run this example server within a secure, \
closed network.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        server.server_close()
        sys.exit(0)
