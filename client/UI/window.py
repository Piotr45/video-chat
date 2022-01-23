import cv2
import imutils
import numpy as np
import socket
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QLabel,
                             QDialog, QVBoxLayout, QGridLayout, QHBoxLayout, QFormLayout, QComboBox)
from PyQt5.QtGui import QIcon, QFont, QPicture, QImage, QPixmap
from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal, QThread
from UI.threads import AuthThread, RecvThread


SERVER_ADDRESS = '0.0.0.0'
SERVER_PORT = 3108


class VideoChatApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.cams = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((SERVER_ADDRESS, SERVER_PORT))
        self.init_ui()

    def init_ui(self):
        self.cams = AppLog(self.server_socket)
        self.cams.show()
        self.close()


class AppLog(QDialog):

    def __init__(self, socket):
        super().__init__()
        self.server_socket = socket
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
        self.thread = AuthThread(self.server_socket, "")

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
        self.thread.buffer = bytes(data, 'UTF-8')
        self.thread.start()
        # self.server_socket.send(bytes(data, 'UTF-8'))

    def _clear_text_boxes(self):
        self.text_boxes["Login"].setText("")
        self.text_boxes["Password"].setText("")

    @pyqtSlot()
    def _on_click_log(self):
        self._send_account_data('LOGIN')
        self._clear_text_boxes()
        respond = self.server_socket.recv(2048)
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
        respond = self.server_socket.recv(2048)
        respond = int(respond.decode('UTF-8'))
        if respond == 1:
            QMessageBox.question(self, 'Register message', "Success!", QMessageBox.Ok, QMessageBox.Ok)
        if respond == -1:
            QMessageBox.question(self, 'Register message', "That nickname is taken!", QMessageBox.Ok, QMessageBox.Ok)
        self._clear_text_boxes()

    def open_video_window(self):
        self.cams = AppVideo(self.server_socket)
        self.cams.show()
        self.close()

    def _switch_back(self):
        self.cams = VideoChatApp()
        self.cams.show()
        self.close()


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
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


class AppVideo(QWidget):

    def __init__(self, socket):
        super().__init__()
        self.server_socket = socket
        self.window_width = 1000
        self.window_height = 800
        self.thread = None
        self.thread2 = None

        self.display_width = 400
        self.display_height = 400
        # Components
        self.image_label = QLabel(self)
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

        self.layout.addWidget(self.image_label, 0, 0)
        self.layout.addWidget(self.cbx_friends, 1, 0)
        self.layout.addWidget(self.bt_call, 1, 1)
        self.layout.addWidget(self.bt_quit, 1, 2)
        self.setLayout(self.layout)

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()
        # self.thread2 = RecvThread(server_socket=self.server_socket)
        # self.thread2.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        # respond = self._server_socket.recv(2048)
        # print(respond.decode('UTF-8'))
        self.server_socket.send(cv_img)
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def _switch_back(self):
        self.cams = AppLog(self.server_socket)
        self.cams.show()
        self.close()
