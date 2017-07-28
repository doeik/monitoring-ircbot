import socket
import threading
import traceback

CREDENTIALS = "NICK Monitoring_System\r\n" \
              "USER moniBot * 8 :This is the monitoring message bot\r\n"
CHANNELS = ["test"]


class IRCBot:
    _serverAddress = None
    _clientSocket = None
    _fd = None
    _running = True
    _lock = None

    def __init__(self, address):
        self._serverAddress = address
        self._clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._fd = self._clientSocket.makefile("r")
        self._lock = threading.Lock()

    def quit(self):
        self._sendMsg("QUIT")
        self._running = False
        # Damit die readline-Methode nicht mehr blockt und der _run-Thread terminieren kann
        try:
            self._clientSocket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self._clientSocket.close()
        except:
            pass

    def __del__(self):
        self.quit()

    def _sendMsg(self, msg):
        res = True
        with self._lock:
            try:
                self._clientSocket.send((msg + "\r\n").encode('UTF-8'))
            except:
                res = False
        return res

    def _waitForEvent(self, action):
        result = False
        while not result and self._running:
            try:
                received = self._fd.readline()
                # super fancy println debugging
                print(received)
                result = action(received)
            except:
                pass

    def _sendPong(self, received):
        res = False
        if received.startswith("PING"):
            self._sendMsg("PONG" + received[4:])
            res = True
        return res

    def _joinChannels(self, received):
        res = False
        # falls die Verbindung geschlossen wird, bevor der Bot im
        # Pong-Loop ist, würde das hier böse abrauchen, daher try-catch
        try:
            status = received.split()[1]
            if status == "376" or status == "422":
                for channel in CHANNELS:
                    self._sendMsg("JOIN #" + channel)
                res = True
        except:
            pass
        return res

    def composeMsgToChannel(self, channel, msg):
        self._sendMsg("PRIVMSG #" + channel + " :" + msg)

    def run(self):
        t = threading.Thread(target=self._run)
        t.start()

    def _run(self):
        try:
            self._clientSocket.connect((self._serverAddress, 6667))
        except Exception:
            traceback.print_exc()
        else:
            with self._fd:
                self._sendMsg(CREDENTIALS)
                self._waitForEvent(self._sendPong)
                self._waitForEvent(self._joinChannels)
                while self._running:
                    self._waitForEvent(self._sendPong)
