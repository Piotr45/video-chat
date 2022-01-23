import sys

from PyQt5.QtWidgets import QApplication
from UI.window import VideoChatApp
from UI.threads import *

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = VideoChatApp()

    sys.exit(app.exec_())
