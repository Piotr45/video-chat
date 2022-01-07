import cv2
import imutils
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QLabel,
                             QDialog, QVBoxLayout, QGridLayout, QHBoxLayout, QFormLayout)
from PyQt5.QtGui import QIcon, QFont, QPicture, QImage, QPixmap
from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal, QThread


class VideoChatApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.cams = None

        self.init_ui()

    def init_ui(self):
        self.cams = AppLog()
        self.cams.show()
        self.close()


class AppLog(QDialog):

    def __init__(self):
        super().__init__()
        self.text_boxes = {}
        self.labels = {}
        self.buttons = {}
        self.title = 'Video Chat'
        self.left = 10
        self.top = 10
        self.width = 400
        self.height = 400
        self.cams = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('pythonlogo.png'))
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

    def _send_account_data(self):
        data = f"{self.text_boxes['Login'].text()}\n{self.text_boxes['Password'].text()}"

    def _clear_text_boxes(self):
        self.text_boxes["Login"].setText("")
        self.text_boxes["Password"].setText("")

    @pyqtSlot()
    def _on_click_log(self):
        QMessageBox.question(self, 'Log in message', "Login", QMessageBox.Ok,
                             QMessageBox.Ok)
        self._clear_text_boxes()
        self.open_video_window()

    @pyqtSlot()
    def _on_click_reg(self):
        QMessageBox.question(self, 'Register message', "Register", QMessageBox.Ok,
                             QMessageBox.Ok)
        self._clear_text_boxes()
        self.open_video_window()

    def open_video_window(self):
        self.cams = AppVideo()
        self.cams.show()
        self.close()

    def _switch_back(self):
        self.cams = AppLog()
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

    def __init__(self):
        super().__init__()
        self.window_width = 1000
        self.window_height = 800

        self.display_width = 400
        self.display_height = 400
        # Labels
        self.image_label = QLabel(self)
        self.txt_lbl = QLabel()
        self.txt_lbl.setText("Friends")
        # Layouts
        self.cam_layout = QGridLayout()
        self.main_layout = QHBoxLayout()
        self.friends_layout = QFormLayout()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Vide Chat Live")
        self.setGeometry(10, 10, self.window_width, self.window_height)
        print(self.size())
        self.image_label.resize(self.display_width, self.display_height)

        self.cam_layout.addWidget(self.image_label, 0, 0)

        self.friends_layout.setVerticalSpacing(10)
        self.friends_layout.addRow(self.txt_lbl)

        self.main_layout.addLayout(self.cam_layout)
        self.main_layout.addLayout(self.friends_layout)
        self.setLayout(self.main_layout)

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
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
        self.cams = AppLog()
        self.cams.show()
        self.close()
