import struct
import pickle

from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import cv2
import socket


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    def run(self):
        while self._run_flag:
            # capture from web cam
            cap = cv2.VideoCapture(0)
            cap.set(3, 320)
            cap.set(4, 240)
            while self._run_flag:
                ret, cv_img = cap.read()
                if ret:
                    self.change_pixmap_signal.emit(cv_img)
            # shut down capture system
            cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class VideoSendThread(QThread):
    def __init__(self, server_socket):
        super().__init__()
        self.conn = server_socket
        self.image = None

    def run(self) -> None:
        a = pickle.dumps(self.image)
        message = struct.pack("Q", len(a)) + a
        # print(self.image.shape)
        self.conn.sendall(message)

    def stop(self):
        self.wait()


class VideoRecvThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, server_socket):
        super().__init__()
        self.conn = server_socket
        self._run_flag = True

    def run(self) -> None:
        self._run_flag = True
        # while self._run_flag:
        data = b""
        payload_size = struct.calcsize("Q")
        while self._run_flag:
            while len(data) < payload_size:
                packet = self.conn.recv(4 * 1024)  # 4K
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += self.conn.recv(4 * 1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            try:
                frame = pickle.loads(frame_data)
            except EOFError:
                print("Ran out of input")
            # print(frame.shape)
            self.change_pixmap_signal.emit(frame)

    def stop(self):
        self._run_flag = False
        self.wait()


class CommandRecvThread(QThread):
    command_respond = pyqtSignal(list)

    def __init__(self, server_socket):
        super().__init__()
        self.conn = server_socket
        self._run_flag = True

    def run(self):
        # print(f"Run command {self.command} with message {self.message}")
        while self._run_flag:
            respond = self.conn.recv(1024 * 2).decode('UTF-8')
            self.command_respond.emit(respond.split('\n'))

    def stop(self):
        self._run_flag = False
        self.wait()


class CommandSendThread(QThread):

    def __init__(self, server_socket):
        super().__init__()
        self.conn = server_socket
        self.command = None
        self.message = None

    def run(self):
        if self.command and self.message:
            self.conn.send(bytes(f"{self.command}\n{self.message}\n", 'UTF-8'))
        elif self.command:
            self.conn.send(bytes(f"{self.command}\n", 'UTF-8'))
        self.reset()

    def stop(self):
        self.wait()

    def reset(self):
        self.command = None
        self.message = None


class AuthThread(QThread):
    def __init__(self, server_socket, buffer):
        super().__init__()
        self.buffer = buffer
        self._server_socket = server_socket

    def run(self) -> None:
        self._server_socket.send(self.buffer)
