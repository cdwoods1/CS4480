from socket import *
import re
import sys
from urlparse import *
from thread import *
from multiprocessing import *
import threading

# Constants that determine the amount of concurrent users that can be on the proxy and the socket buffer size.
MAX_USERS = 1
BUFFER_SIZE = 2048

# The set up to get the port number
if len(sys.argv) != 2:
    print "Invalid number of arguments"
    exit()
serverPort = int(sys.argv[1])


def start_proxy():
    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind(('', serverPort))
        server_socket.listen(MAX_USERS)
        print "server Ready"
    except Exception:
        exit()

    while 1:
        connection_socket, client_addr = server_socket.accept()
        http_request = connection_socket.recv(BUFFER_SIZE)
        while "\n" not in http_request:
            http_request += connection_socket.recv(BUFFER_SIZE)
        # Eventually use multiprocessing to make this part concurrent.
        new_connection(connection_socket, client_addr, http_request)


def new_connection(connection, client_address, http_request):
    try:
        request = http_request.split('\n')
        request_line = request[0].split(" ")
        header_list = request
        del header_list[0]
        # for header in header_list:
        #     if not re.search("^.*: .*", header):
        #         print("Error(400): Invalid Header")
        #         # Create HTTP response to notify user.

        if len(request_line) is not 3:
            print("Error(400): Improperly formatted request line")
            # Create HTTP response to notify user.
        method = request_line[0]
        if re.search("^POST", method) or re.search("^HEAD", method):
            print("Error(501): POST/HEAD not implemented")
            # Create HTTP response to notify user.
        elif not re.search("^GET", method):
            print("Error(400): no method call found")
            # Create HTTP response to notify user.
        else:
            url = request_line[1]
            http_version = request_line[2]
            if not re.search("HTTP/1.0\r", http_version):
                print("Error(400): Request must be HTTP/1.0")
                # Create HTTP response to notify user.
            parsed_url = urlparse(url)

            if not parsed_url.scheme:
                print("Error(400): URL is malformed")
                # Create HTTP response to notify user.

            port = 80
            if parsed_url.port is not None:
                port = parsed_url.port

            get_http_response(parsed_url.geturl(), port, connection, http_request, client_address)
    except Exception, e:
        print(e)
        exit()


def get_http_response(url, port, client_connection, http_request, client_address):
    try:
        http_socket = socket(AF_INET, SOCK_STREAM)
        http_socket.connect((url, port))

        http_request += "Connection: close\r\n"

        http_socket.send(http_request)

        while 1:
            response = http_socket.recv(BUFFER_SIZE)
            print response

            if len(response) > 0:
                client_connection.send(response)
            else:
                break
        http_socket.close()
        client_connection.close()
    except Exception, e:
        print(e)
        exit()


start_proxy()
