# Author: Carson Woods
# CS4480
# U1074881

from socket import *
from optparse import *
import re
import sys
from urlparse import *
from thread import *
import hashlib
import requests

# Constants that determine the amount of concurrent users that can be on the proxy and the socket buffer size.
MAX_USERS = 100
BUFFER_SIZE = 2048

# The set up to get the port number
parser = OptionParser()
parser.add_option("-k", )
serverPort = 2100

# Method that begins the proxy to listen for incoming requests.
def start_proxy():
    server_socket = socket(AF_INET, SOCK_STREAM)
    try:
        # Opening the listening socket.
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind(('', serverPort))
        server_socket.listen(MAX_USERS)
    except Exception:
        # If an error occurs opening the listener socket, the proxy closes.
        exit()
    while 1:
        try:
            # Code to accept a new client, and start a new thread for the new client.
            connection_socket, client_addr = server_socket.accept()
            http_request = connection_socket.recv(BUFFER_SIZE)
            start_new_thread(new_connection, (connection_socket, http_request))
        except Exception:
            http_request.close()


# Method that is called to handle a new client, whenever they join.
def new_connection(connection, http_request):
    try:
        
        # First the request is split into each separate header and the request.
        request = http_request.split('\n')
        # The rest line is parsed to be checked for validity.
        request_line = request[0].split(' ')
        header_list = request
        del header_list[0]

        for header in header_list:
            header = header.replace("\r", "")

            if not re.search("^.*: .*", header) and header is not "":
                connection.send("HTTP/1.0 400 BAD REQUEST\n"
                          + "Content-Type: text/html\n\n"
                          + "<html><body>ERROR(400)\nMALFORMED REQUEST</body></html>\n")
                connection.close()
                return
        if "Connection: close" not in http_request and "Connection: keep-alive" not in http_request:
            http_request += "Connection: close\r\n"
        elif "Connection: keep-alive" in http_request:
            http_request = http_request.replace("Connection: keep-alive", "Connection: close")

        # Test for if the request line only has 3 objects.
        if len(request_line) is not 3:
            connection.send("HTTP/1.0 400 BAD REQUEST\n"
                            + "Content-Type: text/html\n\n"
                            + "<html><body>ERROR(400)\nMALFORMED REQUEST LINE</body></html>\n")
            connection.close
            return
        # Code to ensure the request is a GET request.
        method = request_line[0]
        if re.search("^POST", method) or re.search("^HEAD", method):
            connection.send("HTTP/1.0 501 NOT IMPLEMENTED\n"
                            + "Content-Type: text/html\n\n"
                            + "<html><body>ERROR(501)\nUNIMPLEMENTED METHOD CALL</body></html>\n")
            connection.close()
            return
        elif not re.search("^GET", method):
            connection.send("HTTP/1.0 400 BAD REQUEST\n"
                            + "Content-Type: text/html\n\n"
                            + "<html><body>ERROR(400)\nMALFORMED REQUEST</body></html>\n")
            connection.close()
            return
        else:
            url = request_line[1]
            # Code to ensure that the correct HTTP version is being requested.
            http_version = request_line[2]
            if not re.search("HTTP/1.0\r", http_version):
                connection.send("HTTP/1.0 400 BAD REQUEST\n"
                                + "Content-Type: text/html\n\n"
                                + "<html><body>ERROR(400)\nWRONG HTTP VERSION</body></html>\n")
                connection.close()
                return
            parsed_url = urlparse(url)

            # Code to ensure the URL is valid.
            if not parsed_url.scheme:
                connection.send("HTTP/1.0 400 BAD REQUEST\n"
                                + "Content-Type: text/html\n\n"
                                + "<html><body>ERROR(400)\nMALFORMED URL</body></html>\n")
                connection.close()
                return

            # Code to check whether to use port 80, or a port specified by the user.
            port = 80
            if parsed_url.port is not None:
                port = parsed_url.port

            # The URL is appropriately stripped, so it can be used to connect through a socket.
            url = url.replace("http://", "")
            sep = '/'
            hostname = url.split(sep, 1)[0]

            http_socket = socket(AF_INET, SOCK_STREAM)
            http_socket.connect((hostname, port))
            http_socket.send(http_request)

            # The HTTP response code to parse back the response from the socket.
            while 1:
                response = http_socket.recv(BUFFER_SIZE)
                if len(response) > 0:

                    if re.search("HTTP/1.0 200", response) or re.search("HTTP/1.1 200", response):
                        virus_check_and_send(connection, response)
                    else:
                        connection.send(response)
                else:
                    break

            http_socket.close()
            connection.close()
            return
    except Exception, e:
        connection.close()
        return


# Method that uses Virus Total to check whether the resulting response contains malware. If so,
# the method returns a basic HTTP response letting the user know, otherwise, the method sends back the
# requested response.
def virus_check_and_send(conn_socket, response):
    object_test = response.split("\r\n\r\n")
    params = {'apikey': str(apiKey), 'resource': str(hashlib.md5(object_test[1]).hexdigest())}
    virus_response = requests.get("https://www.virustotal.com/vtapi/v2/file/report", params=params)
    if re.search("\"detected\": true", virus_response.text):
        conn_socket.send("content blocked")
    else:
        conn_socket.send(response)
    return


start_proxy()

