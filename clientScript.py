#!/usr/bin/env python3

import socket
import json
import traceback
from sys import argv

''' Edit this part here '''

UNIXSOCKET = "/run/monitorbot"
CHANNEL = "#test"

def sendToBot(channel, msg):
    clientSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        clientSocket.connect(UNIXSOCKET)
    except Exception:
        traceback.print_exc()
    else:
        with clientSocket:
            with clientSocket.makefile("w") as fd:
                fd.write(json.dumps([channel, msg]) + "\n")
                fd.flush()

def main():
    if len(argv) > 1:
        sendToBot(CHANNEL, argv[1])
    else:
        print("Too few arguments! Exiting...")

if __name__ == "__main__":
    main()