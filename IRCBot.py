import socket
import threading
import traceback
from typing import List, Union

NICK = "Check_MK"
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
        success = True
        with self._sendlock:
            try:
                self._clientSocket.send((msg + "\r\n").encode('UTF-8'))
            except OSError:
                success = False
        return success

    def _waitForEvent(self, action, arguments=()):
        target_reached = False
        while not target_reached and self.isrunning:
            received = self._fd.readline()
            if len(received) == 0:
                self.isrunning = False
            else:
                print(received)
                target_reached = action(received, *arguments)

    def _sendPong(self, received):
        target_reached = False
        if received.startswith("PING"):
            self._sendMsg("PONG" + received[4:])
            target_reached = True
        return target_reached

    def _joinChannels(self, received):
        target_reached = False
        status = received.split()[1]
        if status == "376" or status == "422":
            for channel in self._channels:
                self._sendMsg("JOIN " + channel)
            target_reached = True
        return target_reached

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
        target_reached = False
        try:
            status = received.split()[1]
        except IndexError:
            pass
        else:
            if status == "433":
                target_reached = True
        return target_reached

    def _handleLogin(self, received, nick, retries=3):
        if retries > 0:
            target_reached = self._sendPong(received)
            if not target_reached:
                if self._checkForLoginFail(received):
                    nick = "_" + nick
                    self._sendMsg("NICK " + nick)
                    self._waitForEvent(self._handleLogin, (nick, retries-1))
                    target_reached = True
        else:
            self.quit()
            target_reached = True
        return target_reached

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
                self._sendMsg("NICK " + NICK)
                self._sendMsg("USER " + USER + " * 8 :" + INFO)
                self._waitForEvent(self._handleLogin, (NICK,))
                self._waitForEvent(self._joinChannels)
                while self.isrunning:
                    self._waitForEvent(self._handleServerInput)
