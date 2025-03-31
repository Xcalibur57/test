# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QIcon
from PyQt5 import uic


class Ui(QDialog):
    def __init__(self):
        '''
        Initialisation function for the custom class UI(QDialog) for the Getting Started Widget. 
        '''

        QDialog.__init__(self)
        uic.loadUi('UI/GettingStarted.ui', self)

        self.setWindowTitle('Getting Started')
        self.setWindowIcon(QIcon('_icons/MainWindow.png'))


    def closeEvent(self, event):
        '''
        Handle a closure event for the 'Help' Window.

        Parameters
        ----------
        self: Class
            Parent class for the closure event.
        event: Event
            Not Used

        '''

        print('Closing Help Window.')
        # self.settingsSave()