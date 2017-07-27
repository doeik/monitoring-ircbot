import socket
import traceback
import time


SERVERADDRESS = "192.168.56.101"
CREDENTIALS = "NICK Bot\r\n" \
              "USER blaBot * 8 :testBOT\r\n"


def waitForEvent(fd, socket, action):
    result = None
    while(result == None):
        test = fd.readline()
        print(test)
        result = action(socket, test)
    return result


def sendPong(socket, test):
    res = None
    if test.startswith("PING"):
        socket.send(("PONG" + test[4:]).encode('UTF-8'))
        res = "yay"
    return res


def joinChannel(socket, test):
    res = None
    tmp = test.split()[1]
    if (tmp == "376" or tmp == "422"):
        socket.send("JOIN #test\r\n".encode('UTF-8'))
        res = "yay"
    return res


def main():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect((SERVERADDRESS, 6667))
    except Exception:
        traceback.print_exc()
    else:
        with clientSocket.makefile("r") as fd:
            clientSocket.send(CREDENTIALS.encode('UTF-8'))
            waitForEvent(fd, clientSocket, sendPong)
            waitForEvent(fd, clientSocket, joinChannel)
            while(True):
                waitForEvent(fd, clientSocket, sendPong)




if __name__ == "__main__":
    main()