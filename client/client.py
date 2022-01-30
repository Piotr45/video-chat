import sys
import argparse

from PyQt5.QtWidgets import QApplication
from UI.window import VideoChatApp
from UI.threads import *


ap = argparse.ArgumentParser()
ap.add_argument('-a', '--address', required=True, type=str, help='Server ip address')
ap.add_argument('-p', '--port', required=True, type=int, help='Server port')

args = vars(ap.parse_args())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = VideoChatApp(args["address"], args["port"])

    sys.exit(app.exec_())
