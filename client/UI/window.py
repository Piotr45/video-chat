import pickle
import struct
from datetime import datetime
import time

import cv2
import imutils
import numpy as np
import socket
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QLabel,
                             QDialog, QVBoxLayout, QGridLayout, QHBoxLayout, QFormLayout, QComboBox)
from PyQt5.QtGui import QIcon, QFont, QPicture, QImage, QPixmap
from PyQt5.QtCore import pyqtSlot, Qt
from UI.threads import AuthThread, RecvThread, VideoThread, VideoSendThread, VideoRecvThread


SERVER_ADDRESS = '0.0.0.0'
SERVER_PORT = 3108


class VideoChatApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.cams = None
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_socket.connect((SERVER_ADDRESS, SERVER_PORT))
        self.video_socket.connect((SERVER_ADDRESS, SERVER_PORT))
        print(self.video_socket)
        print(self.command_socket)
        self._send_paring_info()
        self.init_ui()

    def init_ui(self):
        self.cams = AppLog(self.command_socket, self.video_socket)
        self.cams.show()
        self.close()

    def _send_paring_info(self):
        timestamp = int(datetime.timestamp(datetime.now()))
        print(timestamp)
        self.command_socket.send(bytes(f"COMMAND\n", 'UTF-8'))
        self.video_socket.send(bytes(f"VIDEO\n", 'UTF-8'))


class AppLog(QDialog):

    def __init__(self, command_socket, video_socket):
        super().__init__()
        self.command_socket = command_socket
        self.video_socket = video_socket
        # Init dicts for components
        self.text_boxes = {}
        self.labels = {}
        self.buttons = {}
        # Init window settings
        self.title = 'Video Chat'
        self.left = 10
        self.top = 10
        self.width = 400
        self.height = 400
        self.cams = None
        # Init threads
        self.thread_send = AuthThread(self.command_socket, "")

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self._create_components()
        self._assign_on_click_events()

        self.show()

    def _create_components(self):
        self._create_buttons()
        self._create_labels()
        self._create_text_boxes()

    def _create_buttons(self):
        self.buttons["Login"] = QPushButton('Log In', self)
        self.buttons["Login"].move(200, 250)
        self.buttons["Register"] = QPushButton('Register', self)
        self.buttons["Register"].move(100, 250)

    def _create_labels(self):
        self.labels["Login"] = QLabel("Login", self)
        self.labels["Login"].setFont(QFont('Font', 12))
        self.labels["Login"].adjustSize()
        self.labels["Login"].move(self.width / 2 - self.labels["Login"].width() / 2, 70)

        self.labels["Password"] = QLabel("Password", self)
        self.labels["Password"].setFont(QFont('Font', 12))
        self.labels["Password"].adjustSize()
        self.labels["Password"].move(self.width / 2 - self.labels["Password"].width() / 2, 170)

    def _create_text_boxes(self):
        self.text_boxes["Login"] = QLineEdit(self)
        self.text_boxes["Login"].setAlignment(Qt.AlignCenter)
        self.text_boxes["Login"].resize(200, 40)
        self.text_boxes["Login"].move(100, 100)

        self.text_boxes["Password"] = QLineEdit(self)
        self.text_boxes["Password"].setAlignment(Qt.AlignCenter)
        self.text_boxes["Password"].setEchoMode(QLineEdit.Password)
        self.text_boxes["Password"].resize(200, 40)
        self.text_boxes["Password"].move(100, 200)

    def _assign_on_click_events(self):
        self.buttons["Login"].clicked.connect(self._on_click_log)
        self.buttons["Register"].clicked.connect(self._on_click_reg)

    def _send_account_data(self, prefix):
        data = f"{prefix}\n{self.text_boxes['Login'].text()}\n{self.text_boxes['Password'].text()}\n"
        self.thread_send.buffer = bytes(f"{data}", 'UTF-8')
        self.thread_send.start()
        # self.server_socket.send(bytes(data, 'UTF-8'))

    def _clear_text_boxes(self):
        self.text_boxes["Login"].setText("")
        self.text_boxes["Password"].setText("")

    @pyqtSlot()
    def _on_click_log(self):
        self._send_account_data('LOGIN')
        self._clear_text_boxes()
        respond = self.command_socket.recv(2048)
        respond = int(respond.decode('UTF-8'))
        if respond == 1:
            QMessageBox.question(self, 'Log in message', "Login successfully!", QMessageBox.Ok, QMessageBox.Ok)
            self.open_video_window()
        elif respond == -2:
            QMessageBox.question(self, 'Log in message', "Wrong password!", QMessageBox.Ok, QMessageBox.Ok)
        elif respond == -3:
            QMessageBox.question(self, 'Log in message', "There is no user with that login!",
                                 QMessageBox.Ok, QMessageBox.Ok)

    @pyqtSlot()
    def _on_click_reg(self):
        self._send_account_data('REGISTER')
        respond = self.command_socket.recv(2048)
        respond = int(respond.decode('UTF-8'))
        if respond == 1:
            QMessageBox.question(self, 'Register message', "Success!", QMessageBox.Ok, QMessageBox.Ok)
        if respond == -1:
            QMessageBox.question(self, 'Register message', "That nickname is taken!", QMessageBox.Ok, QMessageBox.Ok)
        self._clear_text_boxes()

    def open_video_window(self):
        self.cams = AppVideo(self.command_socket, self.video_socket)
        self.cams.show()
        self.close()

    def _switch_back(self):
        self.cams = VideoChatApp()
        self.cams.show()
        self.close()


class AppVideo(QWidget):

    def __init__(self, command_socket, video_socket):
        super().__init__()
        self.command_socket = command_socket
        self.video_socket = video_socket

        self.thread_video = None
        self.thread_video_2 = None
        self.thread_recv = None
        self.thread_command = None

        self.is_connected = True

        self.window_width = 700
        self.window_height = 400
        self.display_width = 320
        self.display_height = 240
        # Components
        self.image_label = QLabel(self)
        self.connection_label = QLabel(self)
        self.cbx_friends = QComboBox()
        self.bt_call = QPushButton("Call")
        self.bt_quit = QPushButton("Hang up")
        # Layouts
        self.layout = QGridLayout()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Vide Chat Live")
        self.setGeometry(10, 10, self.window_width, self.window_height)

        self.image_label.resize(self.display_width, self.display_height)
        self.connection_label.resize(self.display_width, self.display_height)

        self.layout.addWidget(self.image_label, 0, 0)
        self.layout.addWidget(self.connection_label, 0, 1)
        self.layout.addWidget(self.cbx_friends, 1, 0)
        self.layout.addWidget(self.bt_call, 1, 1)
        self.layout.addWidget(self.bt_quit, 1, 2)
        self.setLayout(self.layout)

        # create the video capture thread
        self.thread_video = VideoThread()
        self.thread_video_2 = VideoSendThread(self.video_socket)
        self.thread_recv = VideoRecvThread(self.video_socket)
        # connect its signal to the update_image slot
        self.thread_video.change_pixmap_signal.connect(self.update_image)
        self.thread_recv.change_pixmap_signal.connect(self.update_call_image)
        # start the thread
        self.thread_video.start()
        self.thread_recv.start()
        #
        self.thread_command = RecvThread(server_socket=self.command_socket)
        self.thread_command.change_active_users.connect(self.update_active_users)
        self.thread_command.start()

    def closeEvent(self, event):
        self.thread_video.stop()
        self.thread_video_2.stop()
        self.thread_recv.stop()
        self.thread_command.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        self.thread_video_2.image = cv_img
        self.thread_video_2.start()

        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    @pyqtSlot(np.ndarray)
    def update_call_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.connection_label.setPixmap(qt_img)

    @pyqtSlot(list)
    def update_active_users(self, usernames):
        self.cbx_friends.clear()
        self.cbx_friends.addItems(usernames)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def _switch_back(self):
        self.cams = AppLog(self.command_socket, self.video_socket)
        self.cams.show()
        self.close()
