#!/usr/bin/env python3

import socket
import os
import stat
import traceback
import threading
import json
from IRCBot import IRCBot

SERVERADDRESS = "192.168.56.101"
# should be /run/monitorbot or something
UNIXSOCKET = "/home/rageagainsthepc/monitorbot"


def handleConnection(clientSocket, bot):
    with clientSocket.makefile("r") as fd:
        try:
            recvdata = fd.readline()
            jsonobj = json.loads(recvdata)
        except ValueError:
            bot.composeMsgToChannel(bot.errorchannel, "Error: Failed to parse json object")
        except:
            bot.composeMsgToChannel(bot.errorchannel,
                                    "Error: An error occured while fetching data from the unix socket.")
        else:
            bot.composeMsgToChannel(jsonobj[0], jsonobj[1])


def interruptConnection(clientSocket):
    try:
        clientSocket.shutdown(socket.SHUT_RDWR)
    except:
        pass


def runServer(bot):
    try:
        os.unlink(UNIXSOCKET)
    except OSError:
        pass
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(UNIXSOCKET)
    os.chmod(UNIXSOCKET, stat.S_IRWXU | stat.S_IRGRP | stat.S_IWGRP)
    server_socket.listen(1)
    while True:
        clientSocket, clientAddress = server_socket.accept()
        with clientSocket:
            connectionThread = threading.Thread(target=handleConnection, args=(clientSocket, bot))
            connectionThread.start()
            connectionTimer = threading.Timer(10.0, interruptConnection, (clientSocket,))
            connectionTimer.start()


def main():
    bot = IRCBot(SERVERADDRESS, "test")
    try:
        bot.run()
        runServer(bot)
    except (KeyboardInterrupt, Exception) as e:
        bot.quit("Exception in main-Thread: " + e.__class__.__name__)
        traceback.print_exc()

if __name__ == "__main__":
    main()
