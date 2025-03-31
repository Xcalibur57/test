# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt, QPoint, QLine, QPointF
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from scipy.optimize import curve_fit

import MTF.Report as Report

import numpy as np
import MISC.Misc_Functions as misc
import MISC.dialog_boxes as dialog
import math
import cv2
import os
import matplotlib.pyplot as plt


def loadImage(ui, fname=None):
    '''
    Parent function to load an image into the main window GUI for AOI Selection.

    Application converts image to 16-bits (if this check-box is checked) and then updates the GUI with the loaded image.

    Parameters
    ----------
    fname: String = None
        Optional string containing the image path to be loaded.

    '''

    if fname == False or fname == None:
        fname = QFileDialog.getOpenFileName(ui, 'Open file', '', 'Image files (*.tif)')
        if fname[0] == '':
            fileSelected = False
        else:
            fileSelected = True
    else:
        fileSelected = True

    if fileSelected:
        try:
            if isinstance(fname, tuple):
                if len(fname) > 1:
                    fname = fname[0]
            elif isinstance(fname, str):
                pass                
            ui.singleMat = cv2.imread(fname, cv2.IMREAD_ANYDEPTH)
            image_load_failed = False
        except:
            image_load_failed = True

        if image_load_failed:
            dialog.messageCritical(ui, 'Error!', 'Image failed to load properly!')
        else:
            if ui.convertTo16BitsCheckBox.isChecked():
                try:
                    if ui.singleMat.dtype == 'uint16':
                        if np.amax(ui.singleMat) <= pow(2, 14):
                            ui.singleMat = ui.singleMat * pow(2, 2)
                    elif ui.singleMat.dtype == 'uint8':
                        ui.singleMat = ui.singleMat * pow(2, 8)
                    elif ui.singleMat.dtype == 'float32':
                        scale_factor = pow(2, 16) / np.amax(ui.singleMat)
                        ui.singleMat = (ui.singleMat * scale_factor).astype('uint16')
                except:
                    dialog.messageCritical(ui, 'Error!', "Image failed to convert to 16-bit!")
    
            try:
                ui.imageWidth.setText(str(ui.singleMat.shape[1]))
                ui.imageHeight.setText(str(ui.singleMat.shape[0]))
                ui.singleImage = QImage(ui.singleMat.data.tobytes(), ui.singleMat.shape[1], ui.singleMat.shape[0], QImage.Format_Grayscale16).convertToFormat(QImage.Format_RGB32)
                ui.image.setPixmap(QPixmap.fromImage(ui.singleImage))
                ui.statusbar.showMessage('Single image loaded!', 2000)
                ui.defineAoiButton.setEnabled(True)
            except:
                dialog.messageCritical(ui, 'Error!', "Failed to load the image into the GUI!")

def BulkAnalyseAndAverage(ui):
    '''
    Load Image (Average MTF) and automatically bulk process.
    '''
    
    dialog.messageInformation(ui, 'Take Note!', "Select a directory which contains folders of field positions and orientations, all at a single focus position.\n\nDirectory MUST contain foldernames that start with \'top\', \'bottom\', \'centre\', \'left\' or \'right\'.\n\nProgram will average all MTF's for each image taken at the focus position.")
    
    ui.bulk_dir_name = QFileDialog.getExistingDirectory(ui, "Select a Directory")
    
    if ui.bulk_dir_name != '':
        for folderName in os.listdir(ui.bulk_dir_name):
            if os.path.isdir(os.path.join(ui.bulk_dir_name, folderName)):
                valid_folder = True
                if folderName.startswith('top'):
                    aoiPoint = QPoint(640, 50)
                elif folderName.startswith('bottom'):
                    aoiPoint = QPoint(640, 974)
                elif folderName.startswith('centre'):
                    aoiPoint = QPoint(640, 512)
                elif folderName.startswith('left'):
                    aoiPoint = QPoint(50, 512)
                elif folderName.startswith('right'):
                    aoiPoint = QPoint(1230, 512)
                else:
                    valid_folder = False

                if valid_folder:
                    list_of_mtfs = []
                    for tif_file in os.listdir(os.path.join(ui.bulk_dir_name, folderName)):
                        if tif_file.endswith('.tif'):
                            loadImage(ui, os.path.join(ui.bulk_dir_name, folderName, tif_file))
                            setAoi(ui, aoiPoint, execute=True)
                            findEdge(ui)
                            analyse(ui, bulk = True)
                            list_of_mtfs.append(ui.FFT)

                    try:
                        array_of_mtfs = np.array(list_of_mtfs)
                        mean_mtf = np.mean(array_of_mtfs, axis = 0)
                        max_mtf = np.amax(array_of_mtfs, axis = 0)
                        mean_half_nyquist = np.interp(32.5, ui.frequency, mean_mtf)
                        max_half_nyquist = np.interp(32.5, ui.frequency, max_mtf)
                        
                        plt.figure(figsize=(16, 9))
                        plt.plot(ui.frequency, mean_mtf, '--b', label = 'Mean')
                        plt.plot(ui.frequency, max_mtf, '--r', label = 'Peak Hold')
                        plt.plot(32.5, mean_half_nyquist, 'ob', label = 'Mean Half-Nyquist = {:.3f}'.format(mean_half_nyquist))
                        plt.plot(32.5, max_half_nyquist, 'or', label = 'Max Half-Nyquist = {:.3f}'.format(max_half_nyquist))
                        plt.xlabel('Spatial Frequency [lp/mm]')
                        plt.ylabel('MTF')
                        plt.ylim(0, 1.05)
                        plt.xlim(0, 65)
                        plt.title(folderName + '_average')
                        plt.grid()
                        plt.legend()
                        plt.savefig(ui.bulk_dir_name + "/averaged_" + folderName + ".png")

                    except:
                        dialog.messageWarning(ui, 'Warning!', 'Something went wrong, and a folder was not processed correctly!')
                else:
                    dialog.messageCritical(ui, 'Error!', 'An invalid folder is in the selected directory, make sure you only have valid folders in the selected directory.')


def AnalyseStack(ui):
    '''
    Load Image Stack and automatically bulk process - And generate a report
    '''

    dialog.messageInformation(ui, 'Take Note!', "Select a directory which contains folders of field positions and orientations, all at a single focus position.\n\nDirectory MUST contain foldernames that start with \'top\', \'bottom\', \'centre\', \'left\' or \'right\'.\n\nProgram will stack all ESF's and calculate a single MTF's from all images, and generate a report.")
        
    ui.bulk_dir_name = QFileDialog.getExistingDirectory(ui, "Select a Directory")
    
    if ui.bulk_dir_name != '':
        for folderName in os.listdir(ui.bulk_dir_name):
            if os.path.isdir(os.path.join(ui.bulk_dir_name, folderName)):

                valid_folder = True
                if folderName.startswith('top'):
                    aoiPoint = QPoint(640, 50)
                elif folderName.startswith('bottom'):
                    aoiPoint = QPoint(640, 974)
                elif folderName.startswith('centre'):
                    aoiPoint = QPoint(640, 512)
                elif folderName.startswith('left'):
                    aoiPoint = QPoint(50, 512)
                elif folderName.startswith('right'):
                    aoiPoint = QPoint(1230, 512)
                else:
                    valid_folder = False
            
                if valid_folder:
                    list_of_raw_positions = []
                    list_of_raw_esf = []
                    ui.number_of_images_processed = 0
            
                    for tif_file in os.listdir(os.path.join(ui.bulk_dir_name, folderName)):
                        if tif_file.endswith('.tif'):
                            loadImage(ui, os.path.join(ui.bulk_dir_name, folderName, tif_file))
                            setAoi(ui, aoiPoint, execute=True)
                            findEdge(ui)
                            analyse(ui, stack = True)
                            
                            list_of_raw_esf.append(ui.EsfRawData)
                            list_of_raw_positions.append(ui.EsfRawPosition)
                            
                            ui.number_of_images_processed += 1
                
                    try:
                        ui.EsfRawData = np.array([item for sublist in list_of_raw_esf for item in sublist])
                        ui.EsfRawPosition = np.array([item for sublist in list_of_raw_positions for item in sublist])
                        fitESFCurve(ui, stacked = True)
                        Report.generateReport(ui, folderName, aoiPoint)
                    except:
                        dialog.messageWarning(ui, 'Warning!', 'Something went wrong, and a folder was not processed correctly!')
                else:
                    dialog.messageCritical(ui, 'Error!', 'An invalid folder is in the selected directory, make sure you only have valid folders in the selected directory.')

def defineAoi(ui):
    '''
    Function to connect the 'clicked' action from the widget to SetAoi function
    '''

    ui.imageWidget.setCursor(Qt.CrossCursor)
    ui.defineAoiButton.setEnabled(False)
    try:
        ui.aoiX.valueChanged.disconnect()
        ui.aoiY.valueChanged.disconnect()
    except:
        pass
    ui.imageWidget.clicked.connect(lambda pressPos: setAoi(ui, pressPos))
    ui.statusbar.showMessage(
        'Click on image to select the Area of Interest')


def setAoi(ui, pressPos, execute=False):
    '''
    Function triggered when 'clicked' is actioned from the image widget.

    Parameters
    ----------
    pressPos: QPoint
        QPoint which must be passed to the function, which indicates the centre of the AOI that has been selected or defined.
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    '''

    ui.statusbar.clearMessage()
    ui.statusbar.showMessage('Area of Interest selected', 2000)

    if not execute:
        ui.imageWidget.clicked.disconnect()

    ui.defineAoiButton.setEnabled(True)
    ui.imageWidget.setCursor(Qt.ArrowCursor)

    ui.aoiX.setValue(pressPos.x())
    ui.aoiY.setValue(pressPos.y())

    if not execute:
        ui.aoiX.valueChanged.connect(lambda: drawAoi(ui))
        ui.aoiY.valueChanged.connect(lambda: drawAoi(ui))

    drawAoi(ui, execute=execute)

def drawAoi(ui, execute=False):
    '''
    Function to draw the AOI in the side-bar of the UI.

    Parameters
    ----------
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    '''

    ui.aoiX.setEnabled(True)
    ui.aoiY.setEnabled(True)

    ui.singleImage = QImage(ui.singleMat.data.tobytes(), ui.singleMat.shape[1], ui.singleMat.shape[0], QImage.Format_Grayscale16).convertToFormat(QImage.Format_RGB32)
    painter = QPainter(ui.singleImage)
    painter.setPen(QPen(Qt.red, 2))
    painter.drawLine(ui.aoiX.value(), ui.aoiY.value() - 20, ui.aoiX.value(), ui.aoiY.value() + 20)
    painter.drawLine(ui.aoiX.value() - 20, ui.aoiY.value(), ui.aoiX.value() + 20, ui.aoiY.value())

    painter.setPen(QPen(Qt.green, 2))

    ui.half_width = int((ui.aoiSize.value() - 1) / 2)

    painter.drawRect(ui.aoiX.value() - ui.half_width, ui.aoiY.value() - ui.half_width, 2 * ui.half_width - 1, 2 * ui.half_width - 1)

    ui.image.setPixmap(QPixmap.fromImage(ui.singleImage))

    top = max(ui.aoiY.value() - ui.half_width, 0)
    bottom = min(ui.aoiY.value() + ui.half_width, 1023)
    left = max(ui.aoiX.value() - ui.half_width, 0)
    right = min(ui.aoiX.value() + ui.half_width, 1279)


    ui.aoiImageMat = np.copy(ui.singleMat[top:bottom+1, left:right+1])

    ui.analyseButton.setEnabled(False)
    updateAoiImage(ui, execute = execute)

def adjustAoi(ui):
    '''
    Function to move the AOI if the AOI is not centred
    '''
    p1 = np.array([ui.edge.x1(), ui.edge.y1(), 0])
    p2 = np.array([ui.edge.x2(), ui.edge.y2(), 0])
    p3 = np.array([(ui.aoiSize.value() - 1) / 2, (ui.aoiSize.value() - 1) / 2, 0])

    d = np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)

    m_edge = ui.edge.dy() / ui.edge.dx()
    
    theta = math.atan(m_edge)

    b_edge = ui.edge.y1() - (m_edge * ui.edge.x1())

    if p3[1] > ((m_edge * p3[0]) + b_edge):
        d = -d
    dX = - math.sin(theta) * d
    dY = math.cos(theta) * d   

    if abs(d) > 2:
        try:
            ui.aoiX.valueChanged.disconnect()
            ui.aoiY.valueChanged.disconnect()
        except:
            pass

        newX = round(ui.aoiX.value() + dX)
        newY = round(ui.aoiY.value() + dY)

        ui.aoiX.setValue(newX)
        ui.aoiY.setValue(newY)

        ui.aoiX.valueChanged.connect(lambda: drawAoi(ui))
        ui.aoiY.valueChanged.connect(lambda: drawAoi(ui))

def updateAoiImage(ui, includeLine=False, execute=False):
    '''
    Function to update the AOI image in the side-bar

    Parameters
    ----------
    includeLine: Boolean
        Optional boolean flag to indicate whether to include the line in the rendered image.
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    '''

    ui.aoiScale = 4

    ui.aoiImageMatScaled = cv2.resize(ui.aoiImageMat, (ui.aoiScale * ui.aoiImageMat.shape[1], ui.aoiScale * ui.aoiImageMat.shape[0]), interpolation=cv2.INTER_AREA)
    
    ui.aoiImageMatScaledStretched = np.multiply(np.subtract(ui.aoiImageMatScaled, np.min(ui.aoiImageMatScaled)),round(65000 / (np.max(ui.aoiImageMatScaled) - np.min(ui.aoiImageMatScaled))))
    
    ui.aoiQImage = QImage(ui.aoiImageMatScaledStretched.data.tobytes(), ui.aoiImageMatScaledStretched.shape[1], ui.aoiImageMatScaledStretched.shape[0], QImage.Format_Grayscale16).convertToFormat(QImage.Format_RGB32)

    if includeLine:
        painter = QPainter(ui.aoiQImage)
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(ui.edgeScaled)
        if execute:
            cv2.imwrite(ui.dir_name + '/aoiImages/' + ui.field + '_' +
                        ui.orientation + '_' + ui.focus + '.tif', ui.aoiImageMatScaled)

    ui.aoiImage.setPixmap(QPixmap.fromImage(ui.aoiQImage))

    if includeLine:
        painter.setPen(QPen(Qt.blue,2))
        origin = [ui.aoiImageMatScaledStretched.shape[0]/2 , ui.aoiImageMatScaledStretched.shape[1]/2, 0]
        p1 = [origin[0] - (ui.aoiScale * ui.lengthOfEdgeLine.value())/2, origin[1] - (ui.aoiScale * ui.normalDistanceFromEdge.value()), 0]
        p2 = [origin[0] + (ui.aoiScale * ui.lengthOfEdgeLine.value())/2, origin[1] - (ui.aoiScale * ui.normalDistanceFromEdge.value()), 0]
        p3 = [origin[0] + (ui.aoiScale * ui.lengthOfEdgeLine.value())/2, origin[1] + (ui.aoiScale * ui.normalDistanceFromEdge.value()), 0]
        p4 = [origin[0] - (ui.aoiScale * ui.lengthOfEdgeLine.value())/2, origin[1] + (ui.aoiScale * ui.normalDistanceFromEdge.value()), 0]

        p1r = misc.rotate2d(origin, p1, ui.angle)
        p2r = misc.rotate2d(origin, p2, ui.angle)
        p3r = misc.rotate2d(origin, p3, ui.angle)
        p4r = misc.rotate2d(origin, p4, ui.angle)

        points = []
        points.append(QPointF(p1r[0], p1r[1]))
        points.append(QPointF(p2r[0], p2r[1]))
        points.append(QPointF(p3r[0], p3r[1]))
        points.append(QPointF(p4r[0], p4r[1]))
        points.append(QPointF(p1r[0], p1r[1]))
        painter.drawPolygon(points,5)

    ui.aoiImage_2.setPixmap(QPixmap.fromImage(ui.aoiQImage))

    ui.findEdgeButton.setEnabled(True)

def findEdge(ui):
    '''
    Function when the 'Find Edge' button is clicked, or when called from a bulk operation
    '''

    cleanEdge(ui)
    try:
        getLine(ui)
        got_line = True
    except:
        dialog.messageCritical(ui, 'Error!', 'Could not find the edge in the AOI!')
        got_line = False

    if got_line:
        if ui.dynamicAoi.isChecked():
            try:
                for i in range(2):
                    adjustAoi(ui)
                    drawAoi(ui)
                    cleanEdge(ui)
                    getLine(ui)
            except:
                dialog.messageCritical(ui, 'Error!', 'Could not move the AOI!')
        
        updateAoiImage(ui, includeLine=True)
        ui.analyseButton.setEnabled(True)


def cleanEdge(ui):
    '''
    Function to clean up the AOI image and remove noise before edge is found   
    '''

    if ui.removeDeadPixels.isChecked():
        aoiImageMat_stddev = np.std(ui.aoiImageMat) * ui.badPixelFactorSpinBox.value()
        for i in range(2):  # repeat the clean to remove the bad pixels effect on averaging
            for x in range(ui.aoiImageMat.shape[1]):
                for y in range(ui.aoiImageMat.shape[0]):
                    if x == 0:  # left edge
                        if y == 0:
                            # top left corner
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x+1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x+1]) > aoiImageMat_stddev):
                                num_neighbours = 3
                                average = ui.aoiImageMat[y+1, x]/num_neighbours + ui.aoiImageMat[y+1, x+1]/num_neighbours + \
                                    ui.aoiImageMat[y, x+1]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                        elif y == ui.aoiImageMat.shape[0] - 1:
                            # bottom left corner
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x+1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x+1]) > aoiImageMat_stddev):
                                num_neighbours = 3
                                average = ui.aoiImageMat[y-1, x]/num_neighbours + ui.aoiImageMat[y-1, x+1]/num_neighbours + \
                                    ui.aoiImageMat[y, x+1]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                        else:
                            # rest of left edge
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x+1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x+1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x+1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x]) > aoiImageMat_stddev):
                                num_neighbours = 5
                                average = ui.aoiImageMat[y-1, x]/num_neighbours + ui.aoiImageMat[y-1, x+1]/num_neighbours + \
                                    ui.aoiImageMat[y, x+1]/num_neighbours + ui.aoiImageMat[y+1, x+1]/num_neighbours + \
                                    ui.aoiImageMat[y+1, x]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                    elif x == ui.aoiImageMat.shape[1] - 1:  # right edge
                        if y == 0:
                            # top right corner
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x-1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x]) > aoiImageMat_stddev):
                                num_neighbours = 3
                                average = ui.aoiImageMat[y, x-1]/num_neighbours + ui.aoiImageMat[y+1, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y+1, x]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                        elif y == ui.aoiImageMat.shape[0] - 1:
                            # bottom right corner
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x-1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x-1]) > aoiImageMat_stddev):
                                num_neighbours = 3
                                average = ui.aoiImageMat[y-1, x]/num_neighbours + ui.aoiImageMat[y-1, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y, x-1]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                        else:
                            # rest of right edge
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x-1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x]) > aoiImageMat_stddev):
                                num_neighbours = 5
                                average = ui.aoiImageMat[y-1, x]/num_neighbours + ui.aoiImageMat[y-1, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y, x-1]/num_neighbours + ui.aoiImageMat[y+1, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y+1, x]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                    else:  # middle section
                        if y == 0:
                            # top edge
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x+1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x+1]) > aoiImageMat_stddev):
                                num_neighbours = 5
                                average = ui.aoiImageMat[y, x-1]/num_neighbours + ui.aoiImageMat[y+1, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y+1, x]/num_neighbours + ui.aoiImageMat[y+1, x+1]/num_neighbours + \
                                    ui.aoiImageMat[y, x+1]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                        elif y == ui.aoiImageMat.shape[0] - 1:
                            # bottom edge
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x+1]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x+1]) > aoiImageMat_stddev):
                                num_neighbours = 5
                                average = ui.aoiImageMat[y, x-1]/num_neighbours + ui.aoiImageMat[y-1, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y-1, x]/num_neighbours + ui.aoiImageMat[y-1, x+1]/num_neighbours + \
                                    ui.aoiImageMat[y, x+1]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)
                        else:
                            # rest of the image
                            if (abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y-1, x+1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y, x+1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x-1]) > aoiImageMat_stddev
                                and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x]) > aoiImageMat_stddev
                                    and abs(ui.aoiImageMat[y, x] - ui.aoiImageMat[y+1, x+1]) > aoiImageMat_stddev):
                                num_neighbours = 8
                                average = ui.aoiImageMat[y-1, x-1]/num_neighbours + ui.aoiImageMat[y-1, x]/num_neighbours + \
                                    ui.aoiImageMat[y-1, x+1]/num_neighbours + ui.aoiImageMat[y, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y, x+1]/num_neighbours + ui.aoiImageMat[y+1, x-1]/num_neighbours + \
                                    ui.aoiImageMat[y+1, x]/num_neighbours + \
                                    ui.aoiImageMat[y+1,
                                                        x+1]/num_neighbours
                                ui.aoiImageMat[y, x] = int(average)

def getLine(ui):
    '''
    Function to handle the housekeeping of find the edge in the AOI Image
    '''

    try:
        m, b = detect_line(ui)
        ui.angle = math.degrees(math.atan(m))
        ui.horizontalMtfEdgeAngleLabel.setText("{:.2f}".format(ui.angle))
        if ui.angle < 0:
            ui.verticalMtfEdgeAngleLabel.setText("{:.2f}".format(ui.angle + 90))
        else:
            ui.verticalMtfEdgeAngleLabel.setText("{:.2f}".format(90 - ui.angle))

        p1, p2 = misc.get_line_from_equation(m, b)
    except:
        dialog.messageCritical(ui, 'Error!', 'Something went wrong in getting the edge in the AOI!')
    ui.edge = QLine(p1[0], p1[1], p2[0], p2[1])
    ui.edgeScaled = QLine(p1[0]*ui.aoiScale, p1[1]*ui.aoiScale, p2[0]*ui.aoiScale, p2[1]*ui.aoiScale)

def detect_line(ui):
    '''
    Function to find the edge in an AOI image
    '''

    edge_x = []
    edge_y = []

    stddev = np.std(ui.aoiImageMat)

    try:
        if (np.std(ui.aoiImageMat[0, :]) < stddev/2) or (np.std(ui.aoiImageMat[ui.aoiImageMat.shape[0] - 1, :]) < stddev/2):
            for i in range(0, ui.aoiImageMat.shape[0]):
                row = ui.aoiImageMat[i, :]
                if np.std(row) < stddev/2:
                    pass
                else:
                    x = np.arange(0, ui.aoiImageMat.shape[1])
                    p0 = [np.amax(row) - np.amin(row), 1,
                        ui.aoiImageMat.shape[1] / 2, np.amin(row)]
                    popt, pcov = curve_fit(
                        misc.f_logistic, x, row, p0=p0, maxfev=10000)
                    edge_x.append(popt[2])
                    edge_y.append(i)
        else:
            for i in range(0, ui.aoiImageMat.shape[0]):
                row = ui.aoiImageMat[i, :]
                x = np.arange(0, ui.aoiImageMat.shape[1])
                p0 = [np.amax(row) - np.amin(row), 1,
                    ui.aoiImageMat.shape[1] / 2, np.amin(row)]
                popt, pcov = curve_fit(
                    misc.f_logistic, x, row, p0=p0, maxfev=10000)
                edge_x.append(popt[2])
                edge_y.append(i)

        if edge_x == []:
            return 0.1, 0
        else:
            p = np.polyfit(edge_x, edge_y, 1)
            return p
    except:
        dialog.messageCritical(ui, 'Error!', 'Could not find the edge in the AOI!')

def analyse(ui, execute = False, bulk = False, stack = False):
    '''
    Function to begin the analysis of the selected AOI.

    Parameters
    ----------
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    bulk: Boolean
        Optional boolean flag to indicate whether this function is being triggered as part of the 'bulk' process.
    stacked: Boolean
        Optional boolean flag to indicate whether this function is being triggered as part of the 'stacked' process.
    '''

    try:
        ui.mtfTabWidget.setCurrentIndex(1)

        xstart = 0
        ystart = 0
        xstop = ui.aoiImageMat.shape[1]
        ystop = ui.aoiImageMat.shape[0]

        a = ui.edge.dy() / ui.edge.dx()
        b = ui.edge.y1() - (a * ui.edge.x1())

        ui.EsfRawData = []
        ui.EsfRawPosition = []

        p1 = np.array([ui.edge.x1(), ui.edge.y1(), 0])
        p2 = np.array([ui.edge.x2(), ui.edge.y2(), 0])

        origin = np.array([(ui.aoiSize.value() - 1) / 2,(ui.aoiSize.value() - 1) / 2, 0])
        p4 = misc.rotate2d(origin, p1, 90)
        p5 = misc.rotate2d(origin, p2, 90)

        for x in range(xstart, xstop, 1):
            for y in range(ystart, ystop, 1):
                p3 = np.array([x, y, 0])

                d = np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)
                if y < ((a * x) + b):
                    d = -d

                dc = np.linalg.norm(np.cross(p5 - p4, p4 - p3)) / np.linalg.norm(p5 - p4)

                if (abs(d) <= ui.normalDistanceFromEdge.value()) and (dc <= ui.lengthOfEdgeLine.value()/2):
                    ui.EsfRawData.append(ui.aoiImageMat[y, x])
                    ui.EsfRawPosition.append(d)

        if not stack:
            ui.plotESF.plotf('ESF', ui.EsfRawData, ui.EsfRawPosition)
            fitESFCurve(ui, execute, bulk)
    except:
        dialog.messageCritical(ui, 'Error!', 'Something went wrong in Analysis')

def fitESFCurve(ui, execute=False, bulk = False, stacked = False):
    '''
    Function to fit a re-sampled curve to the raw ESF Curve.

    Function then runs the EdgeSpec function, followed by the LSFCurve function.

    Parameters
    ----------
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    bulk: Boolean
        Optional boolean flag to indicate whether this function is being triggered as part of the 'bulk' process.
    stacked: Boolean
        Optional boolean flag to indicate whether this function is being triggered as part of the 'stacked' process.
    '''

    try:
        oversampling = ui.oversamplingMultiplier.value()
        maxminD = ui.normalDistanceFromEdge.value()
        num = 1 + (oversampling * maxminD)

        ESFrX = np.linspace(-maxminD, maxminD, num)
        ESFrY = np.zeros(num)

        j = 0
        while j < num:
            sumsI = 0
            sumsN = 0
            for k in range(len(ui.EsfRawPosition)):
                absX = abs(ui.EsfRawPosition[k] - ESFrX[j])
                if absX <= (4 / 7):
                    sumsI += (1 - (7 / 4)*absX)*ui.EsfRawData[k]
                    sumsN += 1 - (7 / 4)*absX
            if sumsN == 0:
                ESFrX = np.delete(ESFrX, j)
                ESFrY = np.delete(ESFrY, j)
                num -= 1
            else:
                ESFrY[j] = sumsI / sumsN
                j += 1
                
        ESFrY = misc.savitzky_golay(ESFrY, ui.oversamplingMultiplier.value() + 1, 3)

        minimum = min(ESFrY)
        maximum = max(ESFrY)
        delta = abs(maximum - minimum)

        d90 = 0
        d10 = 0

        if ESFrY[0] > (minimum + 0.5*delta):
            for x in range(len(ESFrX)):
                if d90 == 0 and ESFrY[x] < minimum + 0.9*delta:
                    d90 = ESFrX[x]
                elif d10 == 0 and ESFrY[x] < minimum + 0.1*delta:
                    d10 = ESFrX[x - 1]
        else:
            for x in range(len(ESFrX)):
                if d10 == 0 and ESFrY[x] > minimum + 0.1*delta:
                    d10 = ESFrX[x]
                elif d90 == 0 and ESFrY[x] > minimum + 0.9*delta:
                    d90 = ESFrX[x - 1]

        dT = ui.tailStartdT.value() * max(abs(d10), abs(d90))
        
        ui.EsfRawData_new = []
        ui.EsfRawPosition_new = []
        ui.EsfRawData_removed = []
        ui.EsfRawPosition_removed = []
        
        if ui.removeNoise.isChecked():
            y_samples = []
            for i in range(len(ui.EsfRawPosition)):
                if ui.EsfRawPosition[i] <= - (3.5 + max(abs(d10), abs(d90))):
                    y_samples.append(ui.EsfRawData[i])
            stddev = np.std(y_samples).astype('uint16')
            scaledSigma = stddev * ui.sigmaScalingSpinBox.value()
            
            for k in range(len(ui.EsfRawPosition)):
                delta = 1
                j_index = 0
                for j in range(num):
                    if abs(ui.EsfRawPosition[k] - ESFrX[j]) < delta:
                        delta = abs(ui.EsfRawPosition[k] - ESFrX[j])
                        j_index = j
                if abs(ESFrX[j_index]) < 2.5:
                    if abs(ESFrY[j_index] - ui.EsfRawData[k]) <= 1.75 * scaledSigma:
                        ui.EsfRawData_new.append(ui.EsfRawData[k])
                        ui.EsfRawPosition_new.append(ui.EsfRawPosition[k])
                    else:
                        ui.EsfRawData_removed.append(ui.EsfRawData[k])
                        ui.EsfRawPosition_removed.append(ui.EsfRawPosition[k])
                else:  
                    if abs(ESFrY[j_index] - ui.EsfRawData[k]) <= scaledSigma:
                        ui.EsfRawData_new.append(ui.EsfRawData[k])
                        ui.EsfRawPosition_new.append(ui.EsfRawPosition[k])
                    else:
    
                        ui.EsfRawData_removed.append(ui.EsfRawData[k])
                        ui.EsfRawPosition_removed.append(ui.EsfRawPosition[k])

            ui.EsfRawData_new = np.array(ui.EsfRawData_new)
            ui.EsfRawPosition_new = np.array(ui.EsfRawPosition_new)
        else:
            ui.EsfRawData_new = ui.EsfRawData
            ui.EsfRawPosition_new = ui.EsfRawPosition

        ui.EsfRawData_removed = np.array(ui.EsfRawData_removed)
        ui.EsfRawPosition_removed = np.array(ui.EsfRawPosition_removed)

        ESFrYnew = np.zeros(num)

        for j in range(num):
            if (not ui.tailSmoothing.isChecked()) or (abs(ESFrX[j]) < dT):
                sumsI = 0
                sumsN = 0
                for k in range(len(ui.EsfRawPosition_new)):
                    X = ui.EsfRawPosition_new[k] - ESFrX[j]
                    if (abs(X) <= 2):
                        sumsI += math.exp(- ui.smoothingAlpha.value() * pow(X, 2)) * ui.EsfRawData_new[k]
                        sumsN += math.exp(- ui.smoothingAlpha.value() * pow(X, 2)) #
                ESFrYnew[j] = sumsI / sumsN
            elif ui.tailSmoothing.isChecked():
                values = []
                for k in range(len(ui.EsfRawPosition_new)):
                    X = ui.EsfRawPosition_new[k] - ESFrX[j]
                    if (abs(X) <= ui.tailSmoothSpinBox.value()):
                        values.append(ui.EsfRawData_new[k])
                ESFrYnew[j] = float(np.mean(values))
        
        ui.EsfPosition = ESFrX

        ui.EsfData = misc.savitzky_golay(ESFrYnew, ui.oversamplingMultiplier.value() + 1, 3)
        
        if ui.tailSmoothing.isChecked():
            ui.plotESF.plotf('ESF', ui.EsfRawData_new, ui.EsfRawPosition_new, ui.EsfData, ui.EsfPosition, tail_start = dT, removed_position = ui.EsfRawPosition_removed, removed_data = ui.EsfRawData_removed)
        else:
            ui.plotESF.plotf('ESF', ui.EsfRawData_new, ui.EsfRawPosition_new, ui.EsfData, ui.EsfPosition, removed_position = ui.EsfRawPosition_removed, removed_data = ui.EsfRawData_removed)

        EdgeSpec(ui, execute)
        LSFCurve(ui, execute)
    except:
        dialog.messageCritical(ui, 'Error!', 'Something went wrong in fitESFCurve.')

def EdgeSpec(ui, execute=False):
    '''
    Function to calculate the specifications of the Edge.

    Parameters
    ----------
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    '''

    try:
        maximum = max(ui.EsfData)
        minimum = min(ui.EsfData)
        delta = maximum - minimum

        percentile10 = 0
        percentile20 = 0
        percentile50 = 0
        percentile80 = 0
        percentile90 = 0

        if ui.EsfData[0] > (minimum + 0.5*delta):
            for x in range(len(ui.EsfPosition)):
                if percentile90 == 0 and ui.EsfData[x] < minimum + 0.9*delta:
                    percentile90 = ui.EsfPosition[x]
                elif percentile80 == 0 and ui.EsfData[x] < minimum + 0.8*delta:
                    percentile80 = ui.EsfPosition[x]
                elif percentile50 == 0 and ui.EsfData[x] < minimum + 0.5*delta:
                    percentile50 = ui.EsfPosition[x]
                elif percentile20 == 0 and ui.EsfData[x] < minimum + 0.2*delta:
                    percentile20 = ui.EsfPosition[x]
                elif percentile10 == 0 and ui.EsfData[x] < minimum + 0.1*delta:
                    percentile10 = ui.EsfPosition[x]
        else:
            for x in range(len(ui.EsfPosition)):
                if percentile10 == 0 and ui.EsfData[x] > minimum + 0.1*delta:
                    percentile10 = ui.EsfPosition[x]
                elif percentile20 == 0 and ui.EsfData[x] > minimum + 0.2*delta:
                    percentile20 = ui.EsfPosition[x]
                elif percentile50 == 0 and ui.EsfData[x] > minimum + 0.5*delta:
                    percentile50 = ui.EsfPosition[x]
                elif percentile80 == 0 and ui.EsfData[x] > minimum + 0.8*delta:
                    percentile80 = ui.EsfPosition[x]
                elif percentile90 == 0 and ui.EsfData[x] > minimum + 0.9*delta:
                    percentile90 = ui.EsfPosition[x]

        ui.width10_90 = abs(percentile90 - percentile10)
        ui.width20_80 = abs(percentile80 - percentile20)

        if execute:
            ui.logRow.append(ui.width10_90)
            ui.logRow.append(ui.width20_80)

        ui.edge10_90.setText(f"{ui.width10_90:.3f}" + " px")
        ui.edge20_80.setText(f"{ui.width20_80:.3f}" + " px")
    except:
        dialog.messageCritical(ui, 'Error!', 'Something went wrong in EdgeSpec')

def LSFCurve(ui, execute=False):
    '''
    Function to generate the LSF curve from the ESF curve, followed by running the MTFCurve function.

    Parameters
    ----------
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    '''

    try:
        ui.LSF = np.gradient(ui.EsfData.astype(np.float64))

        ui.plotLSF.plotf('LSF', ui.LSF, ui.EsfPosition)

        ui.MtfFrequency.setEnabled(True)
        MTFCurve(ui, execute)
    except:
        dialog.messageCritical(ui, 'Error!', 'Something went wrong in LSFCurve')

def MTFCurve(ui, execute=False):
    '''
    Function to generate the MTF curve from the currently active LSF curve data.

    Parameters
    ----------
    ui: Any
        Object which contains the UI of the application, to allow updates to be made to the UI.
    execute: Boolean
        Optional boolean flag to indicate whether this function is being triggered manually (False), or whether it is part of an automated processing sequence (True).
    '''

    try:
        desired_number_of_points = 64

        for i in range(16):
            if pow(2, i) > len(ui.EsfData):
                desired_number_of_points = pow(2, i+1)
                break

        sampling_interval = (ui.pixelSize.value() / 1000) * (max(ui.EsfPosition) - min(ui.EsfPosition)) / len(ui.EsfData)

        ui.FFT = np.split(np.absolute(np.fft.fft(ui.LSF, desired_number_of_points)), 2)[0]

        ui.frequency = np.split(np.fft.fftfreq(desired_number_of_points, d=sampling_interval), 2)[0]

        if ui.MtfFrequency.currentIndex() == 0:
                frequency_max = (1000 / ui.pixelSize.value()) / 4
        elif ui.MtfFrequency.currentIndex() == 1:
            frequency_max = (1000 / ui.pixelSize.value()) / 2

        detector_mtf = []
        truncation_mtf = []
        for f in ui.frequency:
            detector_mtf.append(misc.sinc(ui, f))
            truncation_mtf.append(misc.sinc(ui, (ui.width10_90 * f) / ui.oversamplingMultiplier.value()))

        ui.FFT = ui.FFT / truncation_mtf

        ui.FFT = ui.FFT / ui.FFT[0]

        optical_mtf = ui.FFT / detector_mtf

        ui.plotFFT.plotf('MTF', ui.FFT, ui.frequency, nyquist_range=frequency_max, detector_mtf=detector_mtf, optical_mtf=optical_mtf)

    except:
        dialog.messageCritical(ui, 'Error!', 'Something went wrong in MTFCurve')