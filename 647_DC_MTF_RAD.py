# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 15:43:00 2025

@author: mgoddard
"""

from PyQt5.QtWidgets import QApplication
from UI_Classes.MainWindow import Ui

import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Ui()
    app.exec_()
