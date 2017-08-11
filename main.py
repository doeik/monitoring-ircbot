#!/usr/bin/env python3

import socket
import os
import stat
import threading
import json
from IRCBot import IRCBot

SERVERADDRESS = "192.168.56.101"
UNIXSOCKET = "/run/monitorbot"


def handleConnection(clientSocket, bot):
    with clientSocket.makefile("r") as fd:
        recvdata = fd.readline()
        if len(recvdata) > 0:
            try:
                jsonobj = json.loads(recvdata)
            except ValueError:
                bot.composeMsgTo(bot.errorchannel, "Error: Failed to parse json object")
            else:
                bot.composeMsgTo(jsonobj[0], jsonobj[1])
        else:
            bot.composeMsgTo(bot.errorchannel, "Error: Connection terminated before data could be read.")


def interruptConnection(clientSocket):
    try:
        clientSocket.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def runServer(bot):
    try:
        os.unlink(UNIXSOCKET)
    except OSError:
        pass
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(UNIXSOCKET)
    os.chmod(UNIXSOCKET, stat.S_IRWXU | stat.S_IRGRP | stat.S_IWGRP)
    server_socket.settimeout(10)
    server_socket.listen(1)
    while bot.isrunning:
        try:
            clientSocket, clientAddress = server_socket.accept()
        except socket.timeout:
            pass
        else:
            with clientSocket:
                threading.Thread(target=handleConnection, args=(clientSocket, bot)).start()
                threading.Timer(10.0, interruptConnection, (clientSocket,)).start()


def main():
    with IRCBot(SERVERADDRESS, "#test", errchannel="#test") as bot:
        runServer(bot)


if __name__ == "__main__":
    main()
