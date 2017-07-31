#!/usr/bin/env python3

import socket
import json
import traceback
from sys import argv

UDS_FILE = "/home/rageagainsthepc/monitorbot"

def sendToBot(channel, msg):
    clientSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        clientSocket.connect(UDS_FILE)
    except Exception:
        traceback.print_exc()
    else:
        with clientSocket:
            with clientSocket.makefile("w") as fd:
                fd.write(json.dumps([channel, msg]) + "\n")
                fd.flush()

def main():
    if len(argv) > 2:
        sendToBot(argv[1], argv[2])
    else:
        print("Too few arguments! Exiting...")

if __name__ == "__main__":
    main()