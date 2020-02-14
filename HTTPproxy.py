# Author: Carson Woods
# CS4480
# U1074881

from socket import *
from optparse import *
import re
from urlparse import *
from thread import *
import hashlib
import requests

# Constants that determine the amount of concurrent users that can be on the proxy and the socket buffer size.
MAX_USERS = 100
BUFFER_SIZE = 4096

# The set up to get the port number
parser = OptionParser()
parser.add_option("-k", action="store", type="string", dest="key")
(options, args) = parser.parse_args()
apiKey = options.key
serverPort = 2100


# Method that begins the proxy to listen for incoming requests.
def start_proxy():
    server_socket = socket(AF_INET, SOCK_STREAM)
    # Opening the listening socket.
    server_socket.bind(('', serverPort))
    server_socket.listen(MAX_USERS)
    while 1:
        try:
            # Code to accept a new client, and start a new thread for the new client.
            connection_socket, client_addr = server_socket.accept()
            start_new_thread(new_connection, (connection_socket,))
        except Exception:
            connection_socket.close()


# Method that is called to handle a new client, whenever they join.
def new_connection(connection):
    try:
        http_request = ""
        # First the request is split into each separate header and the request.
        while True:
            http_request += connection.recv(BUFFER_SIZE)
            if http_request.endswith("\n\n") or http_request.endswith("\r\n\r\n"):
                break

        request = http_request.split('\n')
        # The rest line is parsed to be checked for validity.
        request_line = request[0].split(' ')

        method = request_line[0]
        if re.search("^POST", method) or re.search("^HEAD", method):
            connection.send("HTTP/1.0 501 NOT IMPLEMENTED\r\n"
                            + "Content-Type: text/html\r\n" +
                              "Connection: close\r\n\r\n"
                            + "<html><body>ERROR(501) UNIMPLEMENTED METHOD CALL</body></html>")
            connection.close()
            return
        elif not re.search("^GET", method):
            connection.send("HTTP/1.0 400 BAD REQUEST\r\n"
                            + "Content-Type: text/html\r\n" +
                              "Connection: close\r\n\r\n"
                            + "<html><body>ERROR(400) MALFORMED REQUEST</body></html>")
            connection.close()
            return

        header_list = request
        del header_list[0]

        for header in header_list:
            header = header.replace("\r", "")

            if not re.search("^.*: .*", header) and header is not "":
                connection.send("HTTP/1.0 400 BAD REQUEST\r\n"
                                + "Content-Type: text/html\r\n" +
                                  "Connection: close\r\n\r\n"
                                + "<html><body>ERROR(400) MALFORMED REQUEST</body></html>")
                connection.close()
                return
        if re.search("Accept-Encoding: gzip, deflate", http_request):
            http_request = http_request.replace("Accept-Encoding: gzip, deflate\r\n", "")

        if "Connection: close" not in http_request and "Connection: keep-alive" not in http_request:
            http_request += "Connection: close\r\n"
        elif "Connection: keep-alive" in http_request:
            http_request = http_request.replace("Connection: keep-alive", "Connection: close")

        # Test for if the request line only has 3 objects.
        if len(request_line) is not 3:
            connection.send("HTTP/1.0 400 BAD REQUEST\r\n"
                            + "Content-Type: text/html\r\n" +
                              "Connection: close\r\n\r\n"
                            + "<html><body>ERROR(400) MALFORMED REQUEST LINE</body></html>")
            connection.close
            return
        # Code to ensure the request is a GET request.

        url = request_line[1]
        hostname = url.replace("http://", "")
        hostname = hostname.split("/")[0]

        # Code to ensure that the correct HTTP version is being requested.
        http_version = request_line[2]
        if not re.search("HTTP/1.0\r", http_version):
            connection.send("HTTP/1.0 400 BAD REQUEST\r\n"
                                + "Content-Type: text/html\r\n" +
                                  "Connection: close\r\n\r\n"
                                + "<html><body>ERROR(400) WRONG HTTP VERSION</body></html>")
            connection.close()
            return
        # Code to ensure the URL is valid.
        if ":" in hostname:
            hostname, port = hostname.split(":")
        else:
            port = 80

        port = int(port)

        http_socket = socket(AF_INET, SOCK_STREAM)
        try:
            http_socket.connect((hostname, port))
            http_socket.send(http_request)
        except Exception, e:
            print e
            http_socket.close()
            connection.close()
            return

        # The HTTP response code to parse back the response from the socket.
        response = ""
        while 1:
            try:
                res = http_socket.recv(BUFFER_SIZE)
                response += res
                if res is '':
                    break
            except Exception, e:
                print e
                break
        if re.search("HTTP/1.0 200", response) or re.search("HTTP/1.1 200", response):
            virus_check_and_send(connection, response)
        else:
            connection.send(response)
        connection.close()
        http_socket.close()
        return
    except Exception, e:
        print e
        connection.close()
        return


# Method that uses Virus Total to check whether the resulting response contains malware. If so,
# the method returns a basic HTTP response letting the user know, otherwise, the method sends back the
# requested response.
def virus_check_and_send(conn_socket, response):
    object_test = response.split("\r\n\r\n")
    result = hashlib.md5(object_test[1]).hexdigest()
    params = {'apikey': str(apiKey), 'resource': result}
    try:
        virus_response = requests.get("https://www.virustotal.com/vtapi/v2/file/report", params=params)
    except Exception:
        conn_socket.send("HTTP/1.0 500 INTERNAL SERVER ERROR\r\n"
                         + "Content-Type: text/html\r\n"
                         + "Connection: close\r\n\r\n"
                         + "<html><body>Issue with virus request</body></html>")
    if re.search("\"response_code\": 0", virus_response.text):
        conn_socket.send(response)
        return
    if re.search("\"positives\": 0", virus_response.text) and re.search("\"response_code\": 1", virus_response.text):
        conn_socket.send(response)
    elif re.search("\"detected\": true", virus_response.text):
        conn_socket.send("HTTP/1.0 200 OK\r\n"
                         + "Content-Type: text/html\r\n"
                         + "Connection: close\r\n\r\n"
                         + "<html><body>content blocked</body></html>")
    else:
        conn_socket.send(response)
    return


start_proxy()
