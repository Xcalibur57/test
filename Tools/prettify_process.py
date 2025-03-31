# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

import os
import cv2
import csv
import scipy
import numpy as np
import math

# class WorkerThread(QThread):
#     image_count = pyqtSignal(int, bool)
#     message = pyqtSignal(str, bool)

#     def __init__(self):
#         super().__init__()

#     def stop(self):
#         self.is_running = False
    
#     def run(self):
#         self.is_running = True

# def updateProgressDialogProgress(self, progress: (int), _is_running: (bool)):
#     """
#     Slot function to update the progress value in the dialog, which is connected to the emitted signal from the QThread Worker

#     Parameters
#     ----------
#     progress: int
#         Number of Processed images
#     _is_running: bool
#         Flag to show whether the thread is running or not
#     """

#     if _is_running:
#         self.progressDialog.setValue(progress)
#         self.progressDialog.show()

# def updateProgressDialogText(self, text: (str), _is_running: (bool)):
#     """
#     Slot function to update the text in the dialog, which is connected to the emitted signal from the QThread Worker

#     Parameters
#     ----------
#     progress: str
#         Message to display
#     _is_running: bool
#         Flag to show whether the thread is running or not
#     """

#     if _is_running:
#         self.progressDialog.setLabelText(text)
#         self.progressDialog.show()


# def stopThread(self):
#     """
#     Slot function connected to the 'Abort' button on the progress dialog, which will call the function to stop the thread
#     """

#     self.worker.stop()


def Prettify(ui):
    ui.colormaps = []
    
    if ui.checkBoxColormapJet.isChecked():
        ui.colormaps.append(cv2.COLORMAP_JET)
    if ui.checkBoxInferno.isChecked():
        ui.colormaps.append(cv2.COLORMAP_INFERNO)
    if ui.checkBoxRainbow.isChecked():
        ui.colormaps.append(cv2.COLORMAP_RAINBOW)
    if ui.checkBoxHot.isChecked():
        ui.colormaps.append(cv2.COLORMAP_HOT)
    if ui.checkBoxHSV.isChecked():
        ui.colormaps.append(cv2.COLORMAP_HSV)
    if ui.checkBoxViridis.isChecked():
        ui.colormaps.append(cv2.COLORMAP_VIRIDIS)
    if ui.checkBoxOcean.isChecked():
        ui.colormaps.append(cv2.COLORMAP_OCEAN)
    if ui.checkBoxTwilightShifted.isChecked():
        ui.colormaps.append(cv2.COLORMAP_TWILIGHT_SHIFTED)
        
    for image in os.listdir(ui.prettifyInputDirPath.text()):
        if os.path.isfile(os.path.join(ui.prettifyInputDirPath.text(), image)) and image.endswith('.tif'):

            ImageMat = cv2.imread(os.path.join(ui.prettifyInputDirPath.text(), image), cv2.IMREAD_ANYDEPTH)[0:1024, 0:1280]

            if ui.checkBoxAutofillBadPixels.isChecked():
                
                with open(ui.pixelMaskFilePath.text(), 'r', encoding='utf-8-sig') as csv_file:
                    reader = csv.reader(csv_file, delimiter=',')
                    bad_pixels = []
                    for row in reader:
                        bad_pixels.append([int(row[1])-1,int(row[0])-1])
                        
                    for i in range(10):
                        for bad_pixel in bad_pixels:
                            y = bad_pixel[0]
                            x = bad_pixel[1]
                            neighbour_count = 0
                            neighbour_sum = 0
                            for x_delta in [-1, 0, 1]:
                                for y_delta in [-1, 0, 1]:
                                    x_pos = x + x_delta
                                    y_pos = y + y_delta
                                    if (x_pos >= 0 and x_pos <= 1279) and (y_pos >= 0 and y_pos <= 1023) and not (x_pos == x and y_pos == y):
                                        neighbour_count += 1
                                        neighbour_sum += ImageMat[y_pos, x_pos]
                            if neighbour_sum > 0 and neighbour_count > 0:
                                ImageMat[y, x] = int(neighbour_sum / neighbour_count)
            
            if ui.checkBoxInvertImageData.isChecked():
                ImageMat = np.invert(ImageMat)

            if ui.checkBoxDespeckle.isChecked():
                ImageMat = scipy.signal.medfilt2d(ImageMat)
                ImageMat[0, 0] = np.median([ImageMat[0, 1], ImageMat[1, 0], ImageMat[1, 1]])
                ImageMat[1023, 0] = np.median([ImageMat[1022, 0], ImageMat[1022, 1], ImageMat[1023, 1]])
                ImageMat[0, 1279] = np.median([ImageMat[0, 1278], ImageMat[1, 1278], ImageMat[1, 1279]])
                ImageMat[1023, 1279] = np.median([ImageMat[1022, 1279], ImageMat[1022, 1278], ImageMat[1023, 1278]])      

            if ui.checkBoxAutoscaleDynamicRange.isChecked():
                percent_high = np.percentile(ImageMat, 99.97)
                percent_low = np.percentile(ImageMat, 0.07)
                ImageMat = np.clip(((ImageMat - percent_low) * ((math.pow(2, 16) - 1) / (percent_high - percent_low))), 0.0, math.pow(2, 16) - 1).astype('uint16')           
            
            if ui.checkBoxFlipHorizontal.isChecked():
                ImageMat = cv2.flip(ImageMat, 1)

            for colormap in ui.colormaps:
                if colormap == 2:
                    colormapName = 'Jet'
                elif colormap == 9:
                    colormapName = 'HSV'
                elif colormap == 14:
                    colormapName = 'Inferno'
                elif colormap == 4:
                    colormapName = 'Rainbow'
                elif colormap == 11:
                    colormapName = 'Hot'
                elif colormap == 5:
                    colormapName = 'Ocean'
                elif colormap == 16:
                    colormapName = 'Viridis'
                elif colormap == 19:
                    colormapName = 'Twilight Shifted'
                    
                colormapFolderName = os.path.join(ui.prettifyOutputDirPath.text(), os.path.join('Colormapped NUC Images', colormapName))
                if not os.path.exists(colormapFolderName):
                    os.makedirs(colormapFolderName)   
                colorImageMat = cv2.applyColorMap((ImageMat/256).astype('uint8'), colormap)
                cv2.imwrite(os.path.join(colormapFolderName, os.path.basename(image)), colorImageMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))