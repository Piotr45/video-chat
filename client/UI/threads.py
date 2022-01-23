import time

from PyQt5.QtCore import QThread
import numpy as np
import socket


class RecvThread(QThread):
    def __init__(self, server_socket):
        super().__init__()
        self._server_socket = server_socket
        self._run_flag = True
        print("Thread created")

    def run(self):
        print("Thread is running")
        while self._run_flag:
            respond = self._server_socket.recv(2048)
            print(respond.decode('UTF-8'))

    def stop(self):
        self._run_flag = False
        self.wait()


class AuthThread(QThread):
    def __init__(self, server_socket, buffer):
        super().__init__()
        self.buffer = buffer
        self._server_socket = server_socket

    def run(self) -> None:
        self._server_socket.send(self.buffer)
