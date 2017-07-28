import socket
import time
import os
import stat
from IRCBot import IRCBot

SERVERADDRESS = "192.168.56.101"
UDS_FILE = "/home/rageagainsthepc/monitorbot"


def handleConnection(bot, clientSocket):
    with clientSocket.makefile("r") as fd:
        msg = []
        msg.extend(fd.readlines())
        for line in msg:
            bot.composeMsgToChannel("test", line)



# Ich erwarte im Moment nicht mehr als eine Connection auf einmal.
# könnte man bei Gelegenheit aber mal mit threading.Thread(target=handleConnection, (clientSocket, )) machen...
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
        handleConnection(bot, clientSocket)


def main():
    bot = IRCBot(SERVERADDRESS)
    bot.run()
    runServer(bot)


if __name__ == "__main__":
    main()
