import socket
import threading
import traceback
from typing import List, Union

NICK = "Monitoring_System"
USER = "moniBot"
INFO = "This is the monitoring message bot"


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
        except OSError:
            pass
        try:
            self._clientSocket.close()
        except OSError:
            pass

    def _sendMsg(self, msg):
        res = True
        with self._sendlock:
            try:
                self._clientSocket.send((msg + "\r\n").encode('UTF-8'))
            except OSError:
                res = False
        return res

    def _waitForEvent(self, action):
        result = False
        while not result and self.isrunning:
            received = self._fd.readline()
            if len(received) == 0:
                self.isrunning = False
            else:
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

    def _checkForLoginFail(self, received):
        res = False
        try:
            status = received.split()[1]
        except IndexError:
            pass
        else:
            if status == "433":
                res = True
        return res

    # Diese Funktion stört meinen Sinn für Ästhetik, bah! >:[
    def _login(self, nick, user, info, retries=3):
        self._sendMsg("NICK " + nick)
        self._sendMsg("USER " + user + " * 8 :" + info)
        eventReached  = False
        while not eventReached:
            received = self._fd.readline()
            if len(received) > 0:
                eventReached = self._sendPong(received)
                if not eventReached:
                    eventReached = self._checkForLoginFail(received)
                    if eventReached and retries >= 0:
                        self._login("_" + nick, user, info, retries - 1)
            else:
                # Connection dieded, break loop
                eventReached = True

    def _handleServerInput(self, received):
        if not self._sendPong(received):
            decomposed = received.split()
            try:
                statuscode = decomposed[1]
            except IndexError:
                pass
            else:
                if statuscode == "401":
                    self.composeMsgTo(self.errorchannel, "Failed to compose message to " + " ".join(decomposed[3:]))
        # This method shall be active as long as the bot is running
        return False

    def run(self):
        t = threading.Thread(target=self._run)
        t.start()

    def _run(self):
        self._clientSocket.settimeout(10)
        try:
            self._clientSocket.connect((self._serverAddress, 6667))
        except OSError:
            traceback.print_exc()
        else:
            self._clientSocket.settimeout(None)
            with self._fd:
                self._login(NICK, USER, INFO)
                self._waitForEvent(self._joinChannels)
                while self.isrunning:
                    self._waitForEvent(self._handleServerInput)
