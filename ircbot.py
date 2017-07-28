import socket
import time
import os
import stat
from IRCBot import IRCBot


SERVERADDRESS = "192.168.56.101"
UDS_FILE = "/run/monitorbot"


def handleConnection(clientSocket):



def runServer(bot):
    try:
        os.unlink(UDS_FILE)
    except OSError:
        pass
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(UDS_FILE)
    os.chmod(UDS_FILE, stat.S_IRWXU | stat.S_IRGRP | stat.S_IWGRP)
    server_socket.listen(1)
    while True:
        clientSocket, clientAddress = server_socket.accept()
        handleConnection(clientSocket)


def main():
   bot = IRCBot(SERVERADDRESS)
   bot.run()
   while(True):
       print("yay")
       time.sleep(3)



if __name__ == "__main__":
    main()