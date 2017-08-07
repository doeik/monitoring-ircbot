import socket
import threading
import traceback
from typing import List, Union

CREDENTIALS = "NICK Monitoring_System\r\n" \
              "USER moniBot * 8 :This is the monitoring message bot\r\n"


# TODO: Cleaner exception handling, what if nick/user already taken?

class IRCBot:
    _serverAddress = None
    _clientSocket = None
    _fd = None
    isrunning = True
    _sendlock = None
    _privmsglocks = {}
    _channels = []
    errorchannel = None

    def __init__(self, address: str, channels: Union[str, List[str]], errchannel: str = "#errors"):
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

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.quit()
        else:
            traceback.print_exc()
            self.quit("An unhandled Exception occurred: " + exc_type.__name__)
        return True

    def quit(self, reason: str = None):
        if reason is None:
            self._sendMsg("QUIT")
        else:
            self._sendMsg("QUIT :" + reason)
        self.isrunning = False
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
        while not result and self.isrunning:
            received = self._fd.readline()
            if len(received) == 0:
                self.isrunning = False
            else:
                print(received)
                result = action(received)

    def _sendPong(self, received):
        res = False
        if received.startswith("PING"):
            self._sendMsg("PONG" + received[4:])
            res = True
        return res

    def _joinChannels(self, received):
        res = False
        status = received.split()[1]
        if status == "376" or status == "422":
            for channel in self._channels:
                self._sendMsg("JOIN " + channel)
            res = True
        return res

    def composeMsgTo(self, receiver: str, msg: Union[str, List[str]]):
        msgQueue = []
        if type(msg) is list:
            msgQueue.extend(msg)
        else:
            msgQueue.append(msg)
        if receiver.startswith("#"):
            lock = self._privmsglocks.get(receiver, None)
            if lock is not None:
                with lock:
                    for line in msgQueue:
                        self._sendMsg("PRIVMSG " + receiver + " :" + line)
        else:
            for line in msgQueue:
                self._sendMsg("PRIVMSG " + receiver + " :" + line)

    def _handleServerInput(self, received):
        if not self._sendPong(received):
            try:
                decomposed = received.split()
                statuscode = decomposed[1]
            except:
                pass
            else:
                if statuscode == "401":
                    self.composeMsgTo(self.errorchannel, "Failed to compose message to " + " ".join(decomposed[3:]))

    def run(self):
        t = threading.Thread(target=self._run)
        t.start()

    def _run(self):
        self._clientSocket.settimeout(10)
        try:
            self._clientSocket.connect((self._serverAddress, 6667))
        except Exception:
            traceback.print_exc()
        else:
            self._clientSocket.settimeout(None)
            with self._fd:
                self._sendMsg(CREDENTIALS)
                self._waitForEvent(self._sendPong)
                self._waitForEvent(self._joinChannels)
                while self.isrunning:
                    self._waitForEvent(self._handleServerInput)
