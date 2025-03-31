# -*- coding: utf-8 -*-
"""
Created on Fri Dec  2 22:30:08 2022

@author: mgoddard
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, Qt, QPoint

class ClickableWidget(QWidget):
    pressPos = None
    clicked = pyqtSignal(QPoint)
    
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressPos = event.pos()
            

    def mouseReleaseEvent(self, event):
        if (self.pressPos is not None and event.button() == Qt.LeftButton and event.pos() in self.rect()):
            self.clicked.emit(self.pressPos)
        self.pressPos = None