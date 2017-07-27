import socket
import traceback

class IRCBot:
    clientSocket = None
    fd = None

    def __init__(self, address):
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.connect((address, 6667))
        self.fd = self.clientSocket.makefile("r")