# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

import os
import cv2
import glob

class WorkerThread(QThread):
    image_count = pyqtSignal(int, bool)
    message = pyqtSignal(str, bool)

    def __init__(self, tif_files, inputDir, parentDir):
        super().__init__()
        self.tif_files = tif_files
        self.inputDir = inputDir
        self.parentDir = parentDir

    def stop(self):
        self.is_running = False
    
    def run(self):
        self.is_running = True

        self.image_count.emit(0, self.is_running)
        
        image_count_total = len(self.tif_files)

            # read the first image to get dimensions and initialize video writer
        first_tif = cv2.imread(self.tif_files[0], cv2.IMREAD_UNCHANGED)
        
        height, width = first_tif.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # change codec as needed
        video_writer = cv2.VideoWriter(os.path.join(self.parentDir, os.path.basename(self.inputDir) + '.mp4') , fourcc, 25.0, (width, height), True)
        
        image_number = 0
        # process each tif file and write to video
        for tif_file in self.tif_files:
            tif_image = cv2.imread(tif_file, cv2.IMREAD_UNCHANGED)
            video_writer.write(tif_image)
            image_number += 1
            self.image_count.emit(image_number, self.is_running)
            self.message.emit('Processing image ' + str(image_number) + ' of ' + str(image_count_total), self.is_running)
            if not self.is_running:
                break
        video_writer.release()


def updateProgressDialogProgress(self, progress: (int), _is_running: (bool)):
    """
    Slot function to update the progress value in the dialog, which is connected to the emitted signal from the QThread Worker

    Parameters
    ----------
    progress: int
        Number of Processed images
    _is_running: bool
        Flag to show whether the thread is running or not
    """

    if _is_running:
        self.progressDialog.setValue(progress)
        self.progressDialog.show()

def updateProgressDialogText(self, text: (str), _is_running: (bool)):
    """
    Slot function to update the text in the dialog, which is connected to the emitted signal from the QThread Worker

    Parameters
    ----------
    progress: str
        Message to display
    _is_running: bool
        Flag to show whether the thread is running or not
    """

    if _is_running:
        self.progressDialog.setLabelText(text)
        self.progressDialog.show()


def stopThread(self):
    """
    Slot function connected to the 'Abort' button on the progress dialog, which will call the function to stop the thread
    """

    self.worker.stop()

def Video(ui):
    # videoDialog = Video_dialog.Ui()
    # if videoDialog.exec():
    inputDir = ui.videoInputDirPath.text()
    parentDir = os.path.dirname(inputDir)
    
    # get all tif files in the input folder
    tif_files = glob.glob(inputDir + '/*.tif')
    # print(tif_files)

    ui.progressDialog = QProgressDialog(None, 'Abort', 0, len(tif_files), ui)
    ui.progressDialog.setWindowTitle("Please wait...")
    ui.progressDialog.setWindowModality(Qt.ApplicationModal)

    ui.worker = WorkerThread(tif_files, inputDir, parentDir)
    ui.worker.image_count.connect(lambda progress, status: updateProgressDialogProgress(ui, progress, status))
    ui.worker.message.connect(lambda messsage, status: updateProgressDialogText(ui, messsage, status))
    ui.worker.started.connect(ui.progressDialog.show)
    ui.worker.finished.connect(ui.progressDialog.close)
    ui.progressDialog.canceled.connect(lambda: stopThread(ui))
    ui.worker.start()
