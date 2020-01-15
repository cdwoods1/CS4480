from socket import *
import re
import sys
from urlparse import *
from multiprocessing import *
import threading

clients = {}

if len(sys.argv) != 2:
    print "Invalid number of arguments"
    exit()
serverPort = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))
serverSocket.listen(10)
print "server Ready"
while True:
    print "New Loop"
    connectionSocket, clientAddr = serverSocket.accept()
    print 'Accepted connection from:', connectionSocket.getpeername(), ' fd: ', connectionSocket.fileno()
    HTTPRequest = connectionSocket.recv(1024)
    while "\n" not in HTTPRequest:
        HTTPRequest += connectionSocket.recv(1024)

    if re.search("^POST", HTTPRequest) or re.search("^HEAD", HTTPRequest):
        # Send an error, not implemented response. (501)
        connectionSocket.send("Not Implemented(501)")

    elif not re.search("^GET", HTTPRequest):
        # Send a malformed request response. (400)
        connectionSocket.send("Bad Request(400)")
    RequestList = re.split(' ', HTTPRequest)
    FirstRequestLine = HTTPRequest.split('\n')[0]
    URL = FirstRequestLine.split(' ')[1]
    parsedURL = urlparse(URL)
    port = 80
    if parsedURL.port is not None:
        port = parsedURL.port

    HTTPSocket = socket(AF_INET, SOCK_STREAM)
    HTTPSocket.settimeout(3000)
    HTTPSocket.connect((parsedURL.geturl(), port))
    HTTPSocket.sendall(HTTPRequest)

    while 1:
        # receive data from web server
        data = HTTPSocket.recv(4000)

        if len(data) > 0:
            connectionSocket.send(data)  # send to browser/client
        else:
            break
