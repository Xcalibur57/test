# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon

def messageCritical(ui, title, message):
    '''
    Function for displaying a Critical Message

    Parameters
    ----------
    title: String
        Title for the Critical Message
    message: String
        Critical Message text
    '''
            
    dialog = QMessageBox(ui)
    dialog.setWindowTitle(title)
    dialog.setIcon(QMessageBox.Critical)
    dialog.setText(message)
    dialog.setWindowIcon(QIcon('_icons/MainWindow.png'))
    dialog.exec()

def messageInformation(ui, title, message):
    '''
    Function for displaying an Information Message

    Parameters
    ----------
    title: String
        Title for the Information Message
    message: String
        Information Message text
    '''
       
    dialog = QMessageBox(ui)
    dialog.setWindowTitle(title)
    dialog.setIcon(QMessageBox.Information)
    dialog.setText(message)
    dialog.setWindowIcon(QIcon('_icons/MainWindow.png'))
    dialog.exec()

def messageQuestion(ui, title, message):
    '''
    Function for displaying a Question Message

    Parameters
    ----------
    title: String
        Title for the Question Message
    message: String
        Question Message text
    '''
       
    dialog = QMessageBox(ui)
    dialog.setWindowTitle(title)
    dialog.setIcon(QMessageBox.Question)
    dialog.setText(message)
    dialog.setWindowIcon(QIcon('_icons/MainWindow.png'))

def messageWarning(ui, title, message):
    '''
    Function for displaying a Warning Message

    Parameters
    ----------
    title: String
        Title for the Warning Message
    message: String
        Warning Message text
    '''
       
    dialog = QMessageBox(ui)
    dialog.setWindowTitle(title)
    dialog.setIcon(QMessageBox.Warning)
    dialog.setText(message)
    dialog.setWindowIcon(QIcon('_icons/MainWindow.png'))
    dialog.exec()
