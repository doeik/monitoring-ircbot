import socket
import threading
import traceback
from typing import List, Union

CREDENTIALS = "NICK Monitoring_System\r\n" \
              "USER moniBot * 8 :This is the monitoring message bot\r\n"


class IRCBot:
    _serverAddress = None
    _clientSocket = None
    _fd = None
    _running = True
    _sendlock = None
    _privmsglocks = {}
    _channels = []
    errorchannel = None

    def __init__(self, address: str, channels: Union[str, List[str]], errchannel: str="test"):
        self._serverAddress = address
        self._clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._fd = self._clientSocket.makefile("r")
        self._sendlock = threading.Lock()
        # Set up channel list
        if type(channels) is list:
            self._channels.extend(channels)
        else:
            self._channels.append(channels)
        self.errorchannel = errchannel
        if errchannel not in self._channels:
            self._channels.append(errchannel)
        # Create per-channel write locks
        for channel in self._channels:
            self._privmsglocks[channel] = threading.Lock()

    def quit(self, reason: str=None):
        if reason is None:
            self._sendMsg("QUIT")
        else:
            self._sendMsg("QUIT :" + reason)
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

    def _sendMsg(self, msg):
        res = True
        with self._sendlock:
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
                for channel in self._channels:
                    self._sendMsg("JOIN #" + channel)
                res = True
        except:
            pass
        return res

    def composeMsgToChannel(self, channel: str, msg: Union[str, List[str]]):
        msgQueue = []
        if type(msg) is list:
            msgQueue.extend(msg)
        else:
            msgQueue.append(msg)
        lock = self._privmsglocks.get(channel, None)
        if not lock == None:
            with lock:
                for line in msgQueue:
                    self._sendMsg("PRIVMSG #" + channel + " :" + line)

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
