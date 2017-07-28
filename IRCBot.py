import socket
import threading
import traceback

CREDENTIALS = "NICK Bot\r\n" \
              "USER blaBot * 8 :testBOT\r\n"

class IRCBot:
    serverAddress = None
    clientSocket = None
    fd = None
    running = True
    lock = None

    def __init__(self, address):
        self.serverAddress = address
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fd = self.clientSocket.makefile("r")
        self.lock = threading.Lock()


    def quit(self):
        self.sendMsg("QUIT")
        try:
            self.clientSocket.close()
            self.fd.close()
        except:
            pass


    def __del__(self):
        self.quit()


    def sendMsg(self, msg):
        with self.lock:
            try:
                self.clientSocket.send((msg + "\r\n").encode('UTF-8'))
            except Exception:
                traceback.print_exc()



    def waitForEvent(self, action):
        result = False
        while not result:
            received = self.fd.readline()
            # super fancy println debugging
            print(received)
            result = action(received)
        return result


    def sendPong(self, received):
        res = False
        if received.startswith("PING"):
            self.sendMsg("PONG" + received[4:])
            res = True
        return res


    def joinChannel(self, received):
        res = False
        tmp = received.split()[1]
        if (tmp == "376" or tmp == "422"):
            self.sendMsg("JOIN #test")
            res = True
        return res


    def run(self):
        t = threading.Thread(target=self._run)
        t.start()


    def _run(self):
        try:
            self.clientSocket.connect((self.serverAddress, 6667))
        except Exception:
            traceback.print_exc()
        else:
            with self.fd:
                self.sendMsg(CREDENTIALS)
                self.waitForEvent(self.sendPong)
                self.waitForEvent(self.joinChannel)
                while (self.running):
                    self.waitForEvent(self.sendPong)
