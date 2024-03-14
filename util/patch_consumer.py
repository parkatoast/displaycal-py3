# -*- coding utf-8 -*-
"""This is a test utility that consumes patches generated by
ResolveLSPatternGeneratorServer or ResolveCMPatternGeneratorServer.
"""
import random
import socket
import struct
import sys
import time
from xml.etree import ElementTree

from qtpy import QtCore, QtGui, QtWidgets


ADDRESS = ("192.168.178.48", 20002)

# <?xml version="1.0" encoding="utf-8"?>
# <calibration>
#   <color red="512" green="512" blue="512" bits="10"/>
#   <background red="168" green="168" blue="168" bits="10"/>
#   <geometry x="0.3519" y="0.2023" cx="0.3281" cy="0.5076"/>
# </calibration>

def main():
    """The main function that runs the dialog."""
    app = QtWidgets.QApplication(sys.argv)
    dialog = PatchConsumerDialog()
    dialog.accepted.connect(sys.exit)
    dialog.show()
    dialog.run_client()
    app.exec()


class PatchConsumerDialog(QtWidgets.QDialog):
    """The main dialog."""

    def __init__(self, *args, **kwargs):
        super(PatchConsumerDialog, self).__init__(*args, **kwargs)
        self.main_layout = None
        self.color_patch = None
        self.client = None
        self._setup()
        self.app = QtWidgets.QApplication.instance()

    def _setup(self):
        """Create widgets."""
        self.resize(500, 500)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
        )

    def update_color(self, color:QtGui.QColor):
        """Update the color.

        Args:
            color (QtGui.QColor): The color to update to.
        """
        style_sheet = "background-color: rgb({}, {}, {});".format(
            color.red(), color.green(), color.blue()
        )
        print(
            "{:.04f} {:.04f} {:.04f}".format(
                color.redF(),
                color.greenF(),
                color.blueF(),
            )
        )
        self.setStyleSheet(style_sheet)

    def run_client(self):
        """Run the client."""
        self.client = Client()
        self.client.update_color.connect(self.update_color)
        self.client.start()

class Client(QtCore.QThread):
    """The client thread."""

    update_color = QtCore.Signal(QtGui.QColor)

    def __init__(self):
        super(Client, self).__init__()
        self.buffer_size = 16
        self.conn = None

    def run(self):
        """Run the thread."""
        self.conn = socket.create_connection(ADDRESS)
        while True:
            xml_data = b""
            print(xml_data)
            while True:
                data_length_raw = self.conn.recv(4)
                data_length = struct.unpack(">I", data_length_raw)
                data = self.conn.recv(data_length[0])
                color = self.parse_xml_data(data)
                self.update_color.emit(color)

    def parse_xml_data(self, xml_data_raw:bytes) -> QtGui.QColor:
        """Parse the xml data and reutrn the QColor."""
        calibration = ElementTree.fromstring(xml_data_raw)
        color = calibration.find("color")
        red = int(color.attrib["red"])
        green = int(color.attrib["green"])
        blue = int(color.attrib["blue"])
        bit_depth = int(color.attrib["bits"])
        # scale the colors to 16bit
        bit_multiplier = 2**(16 - bit_depth)
        return QtGui.QColor(
            QtGui.QRgba64.fromRgba64(
                red * bit_multiplier,
                green * bit_multiplier,
                blue * bit_multiplier,
                65535,  # alpha
            )
        )

    def quit(self):
        """Quit the thread."""
        self.socket.close()


if __name__ == "__main__":
    main()