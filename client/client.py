import sys
import numpy as np
from socket import *

from PyQt5.QtWidgets import QApplication
from UI.window import AppLog, VideoChatApp, AppVideo


import cv2

SERVER_ADDRESS = '0.0.0.0'
SERVER_PORT = 3108

# vid = cv2.VideoCapture(0)


def send_frame(sock: socket, frame: np.array) -> None:
    def send_single(sock: socket, data: np.array) -> None:
        sock.send(data)
        conf = sock.recv(2048)

    for row in frame:
        send_single(sock, row)

def main():
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((SERVER_ADDRESS, SERVER_PORT))

    while True:
        # ret, frame = vid.read()

        # cv2.imshow("My Cam", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # client_socket.send(frame)

    # vid.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = VideoChatApp()

    sys.exit(app.exec_())
