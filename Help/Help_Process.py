# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

import UI_Classes.Help_Widget as Help_Widget

def GettingStarted(self):
    '''
    Function for handling signals from the MainWindow UI for creating an instance of the Help-Widget.
    '''

    gettingStartedDialog = Help_Widget.Ui()
    if gettingStartedDialog.exec_():
        pass