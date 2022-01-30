import pickle
import signal
import struct
from datetime import datetime
import time

import cv2
import imutils
import os
import numpy as np
import socket
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QLabel,
                             QDialog, QVBoxLayout, QGridLayout, QHBoxLayout, QFormLayout, QComboBox)
from PyQt5.QtGui import QIcon, QFont, QPicture, QImage, QPixmap
from PyQt5.QtCore import pyqtSlot, Qt
from UI.threads import AuthThread, CommandRecvThread, VideoThread, VideoSendThread, VideoRecvThread, CommandSendThread


# SERVER_ADDRESS = '0.0.0.0'
# SERVER_PORT = 3108


class VideoChatApp(QMainWindow):

    def __init__(self, server_address, server_port):
        super().__init__()
        self.cams = None

        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.command_socket.connect((server_address, server_port))
        self.video_socket.connect((server_address, server_port))

        self._send_paring_info()
        self.init_ui()

    def init_ui(self):
        self.cams = AppLog(self.command_socket, self.video_socket)
        self.cams.show()
        self.close()

    def _send_paring_info(self):
        self.command_socket.send(bytes(f"COMMAND\n", 'UTF-8'), socket.MSG_NOSIGNAL)
        self.video_socket.send(bytes(f"VIDEO\n", 'UTF-8'), socket.MSG_NOSIGNAL)


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
        self.command_socket.send(
            bytes(f"PAIR\nCOMMAND\n{self.text_boxes['Login'].text()}\n{self.text_boxes['Password'].text()}\n", 'UTF-8'))
        self.video_socket.send(
            bytes(f"PAIR\nVIDEO\n{self.text_boxes['Login'].text()}\n{self.text_boxes['Password'].text()}\n", 'UTF-8'))
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
        elif respond == -4:
            QMessageBox.question(self, 'Log in message', "This user is already logged in!",
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

        self.is_connected = False
        self.is_camera_on = False
        self.static = True

        self.window_params = {
            "TITLE": "Video Chat Live",
            "WIDTH": 700,
            "HEIGHT": 400
        }
        self.label_params = {
            "WIDTH": 320,
            "HEIGHT": 240
        }

        self.buttons = dict()
        self.labels = dict()
        self.comboboxes = dict()
        self.textboxes = dict()
        self.threads = dict()
        self.layout = None

        self.init_ui()

    def create_components(self):
        self._create_buttons()
        self._create_comboboxes()
        self._create_textboxes()
        self._create_labels()

    def _create_buttons(self):
        self.buttons["CALL"] = QPushButton("Call")
        self.buttons["HANG UP"] = QPushButton("Hang up")
        self.buttons["ADD FRIEND"] = QPushButton("Add friend")
        self.buttons["CAMERA"] = QPushButton("Camera on")

    def _create_comboboxes(self):
        self.comboboxes["FRIENDS"] = QComboBox(self)
        self.comboboxes["FRIENDS"].addItem("Active friends")

    def _create_labels(self):
        self.labels["MY CAMERA"] = QLabel(self)
        self.labels["FRIEND CAMERA"] = QLabel(self)

        self.labels["MY CAMERA"].resize(self.label_params["WIDTH"], self.label_params["HEIGHT"])
        self.labels["FRIEND CAMERA"].resize(self.label_params["WIDTH"], self.label_params["HEIGHT"])

    def _create_textboxes(self):
        self.textboxes["FRIEND NAME"] = QLineEdit(self)

    def create_layout(self):
        self.layout = QVBoxLayout()
        self._add_widgets_to_layout()

    def create_threads(self):
        self.threads["CAMERA UPDATER"] = VideoThread()
        self.threads["COMMAND RECEIVER"] = CommandRecvThread(self.command_socket)
        self.threads["COMMAND SENDER"] = CommandSendThread(self.command_socket)
        self.threads["IMAGE SENDER"] = VideoSendThread(self.video_socket)
        self.threads["IMAGE RECEIVER"] = VideoRecvThread(self.video_socket)

    def _add_widgets_to_layout(self):
        image_layout = QHBoxLayout()
        components_layout = QVBoxLayout()
        line_one_layout = QHBoxLayout()
        line_two_layout = QHBoxLayout()

        image_layout.addWidget(self.labels["MY CAMERA"])
        image_layout.addWidget(self.labels["FRIEND CAMERA"])

        line_one_layout.addWidget(self.buttons["CAMERA"])
        line_one_layout.addWidget(self.buttons["ADD FRIEND"])
        line_one_layout.addWidget(self.textboxes["FRIEND NAME"])

        line_two_layout.addWidget(self.buttons["HANG UP"])
        line_two_layout.addWidget(self.buttons["CALL"])
        line_two_layout.addWidget(self.comboboxes["FRIENDS"])

        components_layout.addLayout(line_one_layout)
        components_layout.addLayout(line_two_layout)
        self.layout.addLayout(image_layout)
        self.layout.addLayout(components_layout)

    def init_ui(self):
        self.setWindowTitle(self.window_params["TITLE"])
        self.setGeometry(10, 10, self.window_params["WIDTH"], self.window_params["HEIGHT"])

        self.create_components()

        self.create_layout()
        self.setLayout(self.layout)

        self.tmp = QPixmap(f"{os.getcwd()}/UI/pp.png").scaled(320, 240, Qt.KeepAspectRatio,
                                                              transformMode=Qt.SmoothTransformation)
        self.tmp2 = cv2.resize(cv2.imread(f"{os.getcwd()}/UI/pp.png"), (320, 240), interpolation=cv2.INTER_AREA)
        # create the video capture thread
        self.create_threads()
        # connect its signal to the update_image slot
        self.threads["CAMERA UPDATER"].change_pixmap_signal.connect(self.update_image)
        self.threads["IMAGE RECEIVER"].change_pixmap_signal.connect(self.update_call_image)
        self.threads["COMMAND RECEIVER"].command_respond.connect(self.update_command)

        self.threads["CAMERA UPDATER"].start()
        if self.is_connected:
            self.threads["IMAGE RECEIVER"].start()
        self._assign_on_click_events()

        self.threads["COMMAND RECEIVER"].start()
        self.threads["COMMAND SENDER"].command = "ACTIVE"
        self.threads["COMMAND SENDER"].start()

    def _assign_on_click_events(self):
        self.buttons["CALL"].clicked.connect(self._on_click_call)
        self.buttons["HANG UP"].clicked.connect(self._on_click_hang_up)
        self.buttons["CAMERA"].clicked.connect(self._on_click_camera)
        self.buttons["ADD FRIEND"].clicked.connect(self._on_click_add_friend)

    @pyqtSlot()
    def _on_click_call(self):
        print("pressed call")
        if self.comboboxes["FRIENDS"] != "Active friends":
            self.threads["COMMAND SENDER"].command = "CALL"
            self.threads["COMMAND SENDER"].message = self.comboboxes["FRIENDS"].currentText()
            self.threads["COMMAND SENDER"].start()

    @pyqtSlot()
    def _on_click_hang_up(self):
        print("pressed hang up")
        self.threads["COMMAND SENDER"].command = "HANG UP"
        self.threads["COMMAND SENDER"].message = None
        self.threads["COMMAND SENDER"].start()

    @pyqtSlot()
    def _on_click_camera(self):
        print("pressed camera")
        if self.is_camera_on:
            self.is_camera_on = False
            self.static = True
            self.buttons["CAMERA"].setText("Camera on")
        else:
            self.is_camera_on = True
            self.static = False
            self.buttons["CAMERA"].setText("Camera off")

    @pyqtSlot()
    def _on_click_add_friend(self):
        print("pressed add friend")
        self.threads["COMMAND SENDER"].message = self.textboxes["FRIEND NAME"].text()
        self.threads["COMMAND SENDER"].command = "ADD-FRIEND"
        self.threads["COMMAND SENDER"].start()

    def closeEvent(self, event):
        self.threads["COMMAND SENDER"].command = "CLOSE"
        self.threads["COMMAND SENDER"].message = None
        self.threads["COMMAND SENDER"].start()
        for thread in self.threads.values():
            if thread.isRunning():
                thread.terminate()
        self.video_socket.close()
        self.command_socket.close()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        if self.static:
            self.labels["MY CAMERA"].setPixmap(self.tmp)
        else:
            qt_img = self.convert_cv_qt(cv_img)
            self.labels["MY CAMERA"].setPixmap(qt_img)

        if self.is_connected:
            if self.static:
                self.threads["IMAGE SENDER"].image = self.tmp2
            else:
                self.threads["IMAGE SENDER"].image = cv_img
            self.threads["IMAGE SENDER"].start()

    @pyqtSlot(np.ndarray)
    def update_call_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        if self.is_connected:
            if not self.threads["IMAGE RECEIVER"].isRunning():
                self.threads["IMAGE RECEIVER"].start()
            qt_img = self.convert_cv_qt(cv_img)
            self.labels["FRIEND CAMERA"].setPixmap(qt_img)
        else:
            self.labels["FRIEND CAMERA"].clear()

    @pyqtSlot(list)
    def update_command(self, respond):
        def handle_adding_friends(respond):
            if int(respond) == 1:
                QMessageBox.question(self, 'Friend list message', "You have a new friend!",
                                     QMessageBox.Ok, QMessageBox.Ok)
            if int(respond) == -1:
                QMessageBox.question(self, 'Friend list message', "There is no user with that login!",
                                     QMessageBox.Ok, QMessageBox.Ok)
            if int(respond) == -2:
                QMessageBox.question(self, 'Friend list message', "This user is already your friend!",
                                     QMessageBox.Ok, QMessageBox.Ok)
            if int(respond) == -3:
                QMessageBox.question(self, 'Friend list message',
                                     "Adding yourself to your friends list is very sad :((",
                                     QMessageBox.Ok, QMessageBox.Ok)
            self.textboxes["FRIEND NAME"].setText("")

        def handle_active_friends(friend_list):
            self.comboboxes["FRIENDS"].clear()
            self.comboboxes["FRIENDS"].addItem("Active friends")
            self.comboboxes["FRIENDS"].addItems(friend_list)

        def handle_call(tmp):
            if int(tmp) == 1:
                self.is_connected = True
                if not self.threads["IMAGE RECEIVER"].isRunning():
                    self.threads["IMAGE RECEIVER"].start()
            if int(tmp) == -1:
                self.is_connected = False
                if self.threads["IMAGE RECEIVER"].isRunning():
                    self.threads["IMAGE RECEIVER"].stop()

        def handle_hang_up(tmp):
            if int(tmp) == 1:
                self.is_connected = False
                self.labels["FRIEND CAMERA"].clear()
                self.threads["IMAGE RECEIVER"].stop()
                self.threads["IMAGE SENDER"].stop()

        print(respond)
        commands_list = ["ADD-FRIEND", "ACTIVE", "CALL", "HANG UP"]
        commands_dict = {command: respond.index(command) for command in commands_list if command in respond}
        sorted_commands = sorted(commands_dict.items(), key=lambda x: x[1])
        index_iterator = iter([idx for _, idx in sorted_commands])
        skip = next(index_iterator)

        for command, index in sorted_commands:
            val = next(index_iterator, -1)
            if val == -1:
                tmp = respond[index:]
            else:
                tmp = respond[index:val]

            if command == "ADD-FRIEND":
                handle_adding_friends(tmp[1])
            elif command == "ACTIVE":
                handle_active_friends(tmp[1:-1])
            elif command == "CALL":
                handle_call(tmp[1])
            elif command == "HANG UP":
                handle_hang_up(tmp[1])

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.label_params["WIDTH"], self.label_params["HEIGHT"],
                                        Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        return QPixmap.fromImage(p)

    def _switch_back(self):
        self.cams = AppLog(self.command_socket, self.video_socket)
        self.cams.show()
        self.close()
