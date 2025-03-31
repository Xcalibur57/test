# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from scipy.signal import savgol_filter
import MISC.dialog_boxes as dialog
import matplotlib.pyplot as plt
from datetime import datetime
import os
import csv
import numpy as np
import cv2
import pandas as pd

class WorkerThread(QThread):
    """
    Worker Thread Class, which subclasses QThread to perform the Radiometry analysis outside of the User Interface Event Loop
    """

    image_count = pyqtSignal(int, bool)
    message = pyqtSignal(str, bool)


    def __init__(self, inputDirPath: str, badPixelMask: str, image_count_num: int, images_per_folder: int,
                 radiometrySaveCSVFileCheckBox: bool, radiometrySavePlotsCheckBox: bool, radiometryDisplayPlotsCheckBox: bool,
                 averagingMeanCheckBox: bool, averagingMedianCheckBox: bool, averagingModeCheckBox: bool,
                 ignoreBadPixelsCheckBox: bool, ignoreSaturatedPixelsCheckBox: bool, ignoreNonResponsivePixelsCheckBox: bool, ignoreConstantPixelsCheckBox: bool,
                 signalBinsSpinBox: int, signalMinSpinBox: int, signalMaxSpinBox: int,
                 noiseBinsSpinBox: int, noiseMinSpinBox: int, noiseMaxSpinBox: int,
                 imagesToProcessSpinBox: int):
        
        """ Worker Thread Initialisation Function"""

        super().__init__()
        self.inputDirPath = inputDirPath
        self.badPixelMask = badPixelMask
        self.image_count_num = image_count_num
        self.images_per_folder = images_per_folder
        self.radiometrySaveCSVFileCheckBox = radiometrySaveCSVFileCheckBox
        self.radiometrySavePlotsCheckBox = radiometrySavePlotsCheckBox
        self.radiometryDisplayPlotsCheckBox = radiometryDisplayPlotsCheckBox
        self.averagingMeanCheckBox = averagingMeanCheckBox
        self.averagingMedianCheckBox = averagingMedianCheckBox
        self.averagingModeCheckBox = averagingModeCheckBox
        self.ignoreBadPixelsCheckBox = ignoreBadPixelsCheckBox
        self.ignoreSaturatedPixelsCheckBox = ignoreSaturatedPixelsCheckBox
        self.ignoreNonResponsivePixelsCheckBox = ignoreNonResponsivePixelsCheckBox
        self.ignoreConstantPixelsCheckBox = ignoreConstantPixelsCheckBox
        self.signalBinsSpinBox = signalBinsSpinBox
        self.signalMinSpinBox = signalMinSpinBox
        self.signalMaxSpinBox = signalMaxSpinBox
        self.noiseBinsSpinBox = noiseBinsSpinBox
        self.noiseMinSpinBox = noiseMinSpinBox
        self.noiseMaxSpinBox = noiseMaxSpinBox
        self.imagesToProcessSpinBox = imagesToProcessSpinBox


    def stop(self):
        """ Set Flag to Stop Worker Thread"""

        self._is_running = False


    def run(self):
        """ Run function for Worker Thread, called automatically when WorkerThread.start() is called"""
       
        self._is_running = True

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")

        # Update Progress Dialog Progress
        self.image_count.emit(0, self._is_running)
        
        # Check if Bad Pixels (according to the Bad Pixel Map) should be ignored
        if self.ignoreBadPixelsCheckBox:
            with open(self.badPixelMask, 'r', encoding='utf-8-sig') as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                bad_pixels = []
                for row in reader:
                    bad_pixels.append([int(row[1])-1,int(row[0])-1])

        # Check if thread should save results to CSV file
        if self.radiometrySaveCSVFileCheckBox:
            # Create temporary lists to store results
            df_int_times = []
            df_temps = []
            if self.averagingMeanCheckBox:
                df_signal_mean = []
                df_noise_mean = []
            if self.averagingMedianCheckBox:
                df_signal_median = []
                df_noise_median = []
            if self.averagingModeCheckBox:
                df_signal_mode = []
                df_noise_mode = []
            
        total_image_number = 0

        image_count = self.imagesToProcessSpinBox

        imageArr = np.zeros((image_count, 1024, 1280))
    
        # Loop through items in the inputDirPath directory
        for folderNameK in os.listdir(self.inputDirPath):
            # Check if Radiometry Process has been cancelled
            if not self._is_running:
                break
            
            # Check item is a folder, and ends with a 'K', to check it is a temperature folder
            if os.path.isdir(os.path.join(self.inputDirPath, folderNameK)) and folderNameK.endswith('K'):   

                # Loop through items in the folderNameK folder 
                for folderNameMs in os.listdir(os.path.join(self.inputDirPath, folderNameK)):
                    # Check if Radiometry Process has been cancelled
                    if not self._is_running:
                        break

                    # Check item is a folder, and ends with an 'ms', to check it is an integration time folder
                    if os.path.isdir(os.path.join(self.inputDirPath, folderNameK, folderNameMs)) and folderNameMs.endswith('ms'):

                        image_dir = os.path.join(self.inputDirPath, folderNameK, folderNameMs)
                        image_number = 0
                        
                        # Loop through all items in the folderNameMs folder
                        for image in os.listdir(image_dir):
                            # Check if Radiometry Process has been cancelled
                            if not self._is_running:
                                break

                            # Check item is a file, and ends with '.tif', to check it is an image file
                            if os.path.isfile(os.path.join(image_dir, image)) and image.endswith('.tif'):

                                # Add cropped image to the image stack array - cropped to the active area, ignoring any additional rows or columns (ancilliary data)
                                imageArr[image_number] = cv2.imread(os.path.join(image_dir, image), cv2.IMREAD_ANYDEPTH)[0:1024, 0:1280]
                                
                                # If Bad Pixels are to be ignored, then set each Bad Pixel's value to 'NaN'
                                if self.ignoreBadPixelsCheckBox:
                                    for bad_pixel in bad_pixels:
                                        (imageArr[image_number])[bad_pixel[0], bad_pixel[1]] = float('nan')
                                    
                                image_number += 1
                                total_image_number += 1

                                # Update Progress Dialog Progress
                                self.image_count.emit(total_image_number, self._is_running)

                                # Update Progress Dialog Message
                                self.message.emit('Processing image ' + str(total_image_number) + ' of ' + str(self.image_count_num), self._is_running)

                                # Precautionary check to end the loop through the folderNameMs folder, once the correct number of images has been processed
                                # This is to handle the possible case that some folders have more images than others
                                if image_number == image_count:
                                    break
                        
                        # Check if Radiometry Process has been cancelled
                        if not self._is_running:
                            break

                        # Update Progress Dialog Message
                        self.message.emit('Calculating Signal Statistics...', self._is_running)

                        # If Mode is required, or generating and/or saving plots, then prepare histogram of image data for processing                        
                        if self.averagingModeCheckBox or self.radiometryDisplayPlotsCheckBox or self.radiometrySavePlotsCheckBox:
                            counts, bins = np.histogram(imageArr, self.signalBinsSpinBox, (self.signalMinSpinBox, self.signalMaxSpinBox))
                            # re-sample bins
                            newBins = []
                            for i in range(len(bins) - 1):
                                newBins.append((bins[i] + bins[i+1])/2)

                        # If Mean Averaginig is required, calculate mean of signal across all images and pixels
                        if self.averagingMeanCheckBox:
                            mean = np.nanmean(imageArr)

                        # If Median Averaging is required, calculate median of signal across all images and pixels
                        if self.averagingMedianCheckBox:
                            median = np.nanmedian(imageArr)

                        # If Mode Averaging is required, apply filter to the histogram, and take highest point as Mode
                        if self.averagingModeCheckBox:
                            newCount = savgol_filter(counts, 75, 2)
                            mode = newBins[np.argmax(newCount)]

                        min_a = np.nanmin(imageArr)
                        max_a = np.nanmax(imageArr)

                        # If saving data to file, store in temporary lists
                        if self.radiometrySaveCSVFileCheckBox:
                            df_int_times.append(int(folderNameMs[:-2]))
                            df_temps.append(int(folderNameK[:3]))
                        
                            if self.averagingMeanCheckBox:
                                df_signal_mean.append(mean)
                            if self.averagingMedianCheckBox:
                                df_signal_median.append(int(median))
                            if self.averagingModeCheckBox:
                                df_signal_mode.append(int(mode))

                        # If displaying and/or saving plots
                        if self.radiometrySavePlotsCheckBox or self.radiometryDisplayPlotsCheckBox:

                            # Update Progress Dialog Message
                            self.message.emit('Generating Signal Plots...', self._is_running)
                            
                            plt.figure(figsize=(16, 9))
                            plt.stairs(counts, bins, fill = True)
                            if self.averagingModeCheckBox:
                                plt.plot(newBins, newCount, 'r-')
                            plt.xlim(0, np.power(2,14))
                            plt.yscale('log')
                            plt.xlabel('ADC Signal [ADU]')
                            plt.ylabel('PDF')
                            plt.ylim(bottom=1)
                            plt.title(str(image_count) + ' Images Pixel Values - ' + os.path.basename(self.inputDirPath) + '/' + folderNameK + '/' + folderNameMs + ' - Log10')
                            plt.xticks(ticks = np.linspace(0, np.power(2,14), num=9, endpoint=True))
                            if self.averagingMedianCheckBox:
                                plt.plot([] ,[] ,' ', label='Median: {:.0f}'.format(median))
                            if self.averagingMeanCheckBox:
                                plt.plot([] ,[] ,' ', label='Mean: {:.2f}'.format(mean))
                            if self.averagingModeCheckBox:
                                plt.plot([], [], ' ', label='Mode: {:.0f}'.format(mode))
                            plt.plot([] ,[] ,' ', label='Min: {:.0f}'.format(min_a))
                            plt.plot([] ,[] ,' ', label='Max: {:.0f}'.format(max_a))
                            plt.legend()
                            plt.grid()
                            if self.radiometrySavePlotsCheckBox:
                                plt.savefig(self.inputDirPath + '/PixelValues_Log10_raw' + folderNameK + '_' + folderNameMs + '.png')
                            
                            plt.figure(figsize=(16, 9))
                            plt.stairs(counts, bins, fill = True)
                            if self.averagingModeCheckBox:
                                plt.plot(newBins, newCount, 'r-')
                            plt.xlim(0, np.power(2,14))
                            plt.yscale('linear')
                            plt.xlabel('ADC Signal [ADU]')
                            plt.ylabel('PDF')
                            plt.title(str(image_count) + ' Images Pixel Values - ' + os.path.basename(self.inputDirPath) + '/' + folderNameK + '/' + folderNameMs + ' - Linear')
                            plt.xticks(ticks = np.linspace(0, np.power(2,14), num=9, endpoint=True))
                            if self.averagingMedianCheckBox:
                                plt.plot([] ,[] ,' ', label='Median: {:.0f}'.format(median))
                            if self.averagingMeanCheckBox:
                                plt.plot([] ,[] ,' ', label='Mean: {:.2f}'.format(mean))
                            if self.averagingModeCheckBox:
                                plt.plot([], [], ' ', label='Mode: {:.0f}'.format(mode))
                            plt.plot([] ,[] ,' ', label='Min: {:.0f}'.format(min_a))
                            plt.plot([] ,[] ,' ', label='Max: {:.0f}'.format(max_a))
                            plt.legend()
                            plt.grid()
                            if self.radiometrySavePlotsCheckBox:
                                plt.savefig(self.inputDirPath + '/PixelValues_Linear_raw' + folderNameK + '_' + folderNameMs + '.png')

                        # Update Progress Dialog Message
                        self.message.emit('Calculating Noise Statistics...', self._is_running)

                        # Calculate the standard deviation of each pixel through all images
                        std_dev_of_each_pixelArr = np.nanstd(imageArr, axis = 0)

                        # If Mode is required, or generating and/or saving plots, then prepare histogram of image data for processing  
                        if self.averagingModeCheckBox or self.radiometryDisplayPlotsCheckBox or self.radiometrySavePlotsCheckBox:
                            counts, bins = np.histogram(std_dev_of_each_pixelArr, self.noiseBinsSpinBox, (self.noiseMinSpinBox, self.noiseMaxSpinBox))
                            # Resample Bins
                            newBins = []
                            for i in range(len(bins) - 1):
                                newBins.append((bins[i] + bins[i+1])/2)

                        # If Mean Averaginig is required, calculate mean standard deviation
                        if self.averagingMeanCheckBox:
                            mean = np.nanmean(std_dev_of_each_pixelArr)
                        # If Median Averaginig is required, calculate median standard deviation
                        if self.averagingMedianCheckBox:
                            median = np.nanmedian(std_dev_of_each_pixelArr)
                        # If Mode Averaging is required, apply filter to the histogram, and take highest point as Mode
                        if self.averagingModeCheckBox:
                            newCount = savgol_filter(counts, 17, 2)
                            mode = newBins[np.argmax(newCount)]

                        # Check if Radiometry Process has been cancelled
                        if not self._is_running:
                            break
                        
                        # If saving data to file, store in temporary lists
                        if self.radiometrySaveCSVFileCheckBox:
                            if self.averagingMeanCheckBox:
                                df_noise_mean.append(mean)
                            if self.averagingMedianCheckBox:
                                df_noise_median.append(median)
                            if self.averagingModeCheckBox:
                                df_noise_mode.append(mode)

                        # If displaying and/or saving plots
                        if self.radiometrySavePlotsCheckBox or self.radiometryDisplayPlotsCheckBox:

                            # Update Progress Dialog Message
                            self.message.emit('Generating Noise Plots...', self._is_running)

                            plt.figure(figsize=(16, 9))
                            plt.stairs(counts, bins, fill = True)
                            if self.averagingModeCheckBox:
                                plt.plot(newBins, newCount, 'r-')
                            plt.xlim(0, self.noiseMaxSpinBox)
                            plt.yscale('log')
                            plt.xlabel('ADC Signal [ADU]')
                            plt.ylabel('PDF')
                            plt.ylim(bottom=1)
                            plt.title('Temporal Standard Deviation - ' + os.path.basename(self.inputDirPath) + '/' + folderNameK + '/' + folderNameMs + ' - Log10')
                            plt.xticks(ticks = np.linspace(0, self.noiseMaxSpinBox, num=9, endpoint=True))
                            if self.averagingMedianCheckBox:
                                plt.plot([] ,[] ,' ', label='Median: {:.2f}'.format(median))
                            if self.averagingMeanCheckBox:
                                plt.plot([] ,[] ,' ', label='Mean: {:.2f}'.format(mean))
                            if self.averagingModeCheckBox:
                                plt.plot([], [], ' ', label='Mode: {:.2f}'.format(mode))
                            plt.legend()
                            plt.grid()
                            if self.radiometrySavePlotsCheckBox:
                                plt.savefig(self.inputDirPath + '/TemporalNoise_Log10_raw' + folderNameK + '_' + folderNameMs + '.png')
                            
                            plt.figure(figsize=(16, 9))
                            plt.stairs(counts, bins, fill = True)
                            if self.averagingModeCheckBox:
                                plt.plot(newBins, newCount, 'r-')
                            plt.xlim(0, self.noiseMaxSpinBox)
                            plt.yscale('linear')
                            plt.xlabel('ADC Signal [ADU]')
                            plt.ylabel('PDF')
                            plt.title('Temporal Standard Deviation - ' + os.path.basename(self.inputDirPath) + '/' + folderNameK + '/' + folderNameMs + ' - Linear')
                            plt.xticks(ticks = np.linspace(0, self.noiseMaxSpinBox, num=9, endpoint=True))
                            if self.averagingMedianCheckBox:
                                plt.plot([] ,[] ,' ', label='Median: {:.2f}'.format(median))
                            if self.averagingMeanCheckBox:
                                plt.plot([] ,[] ,' ', label='Mean: {:.2f}'.format(mean))
                            if self.averagingModeCheckBox:
                                plt.plot([], [], ' ', label='Mode: {:.2f}'.format(mode))
                            plt.legend()
                            plt.grid()
                            if self.radiometrySavePlotsCheckBox:
                                plt.savefig(self.inputDirPath + '/TemporalNoise_Linear_raw' + folderNameK + '_' + folderNameMs + '.png')

                        # Check if Radiometry Process has been cancelled
                        if not self._is_running:
                            break

        # Check if thread should save results to CSV file
        if self.radiometrySaveCSVFileCheckBox:
            # Handle the edge case that the temporary storage lists are not all the same size
            lengths = [len(df_int_times),
                       len(df_temps)]
            if self.averagingMeanCheckBox:
                lengths.append(len(df_signal_mean))
                lengths.append(len(df_noise_mean))
            if self.averagingMedianCheckBox:
                lengths.append(len(df_signal_median))
                lengths.append(len(df_noise_median))
            if self.averagingModeCheckBox:
                lengths.append(len(df_signal_mode))
                lengths.append(len(df_noise_mode))
            min_length = min(lengths)

            # Prepare Data for saving to file
            data = {
                "integration_time[ms]": df_int_times[:min_length],
                "bb_temperature[K]": df_temps[:min_length],
                "signal_mean[ADU]": df_signal_mean[:min_length],
                "signal_median[ADU]": df_signal_median[:min_length],
                "signal_mode[ADU]": df_signal_mode[:min_length],
                "noise_mean[ADU]": df_noise_mean[:min_length],
                "noise_median[ADU]": df_noise_median[:min_length],
                "noise_mode[ADU]": df_noise_mode[:min_length]
            }
            df = pd.DataFrame(data)
            df.to_csv(self.inputDirPath + '/data_' + timestamp + '.csv', sep=',', index=False, encoding='utf-8')


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


def RadiometryWorkerStart(ui):
    """
    Slot function connected to the Radiometry Process Button in the main UI
    Function sets up the worker thread and checks the number of images to process before
    starting the new thread.
    """

    image_count_num = 0
    images_per_folder = []

    if ui.radiometryInputDirPath.text() != '' and os.path.isdir(ui.radiometryInputDirPath.text()):
        if ui.pixelMaskFilePath_2.text() != '' and os.path.exists(ui.pixelMaskFilePath_2.text()):
            for folderNameK in os.listdir(ui.radiometryInputDirPath.text()):
                if os.path.isdir(os.path.join(ui.radiometryInputDirPath.text(), folderNameK)):
                    for folderNameMs in os.listdir(os.path.join(ui.radiometryInputDirPath.text(), folderNameK)):
                        if os.path.isdir(os.path.join(ui.radiometryInputDirPath.text(), folderNameK, folderNameMs)) and folderNameMs.endswith('ms'):
                            temp_images_per_folder = 0
                            for image in os.listdir(os.path.join(ui.radiometryInputDirPath.text(), folderNameK, folderNameMs)):
                                if os.path.isfile(os.path.join(ui.radiometryInputDirPath.text(), folderNameK, folderNameMs, image)) and image.endswith('.tif'):
                                    image_count_num += 1
                                    temp_images_per_folder += 1
                                    if temp_images_per_folder == ui.imagesToProcessSpinBox.value():
                                        break
                            images_per_folder.append(temp_images_per_folder)

            ui.progressDialog = QProgressDialog(None, 'Abort Analysis', 0, image_count_num, ui)
            ui.progressDialog.setWindowTitle("Please wait...")
            ui.progressDialog.setWindowModality(Qt.ApplicationModal)

            ui.worker = WorkerThread(ui.radiometryInputDirPath.text(), ui.pixelMaskFilePath_2.text(), image_count_num, images_per_folder, 
                                     ui.radiometrySaveCSVFileCheckBox.isChecked(), ui.radiometrySavePlotsCheckBox.isChecked(), ui.radiometryDisplayPlotsCheckBox.isChecked(),
                                     ui.averagingMeanCheckBox.isChecked(), ui.averagingMedianCheckBox.isChecked(), ui.averagingModeCheckBox.isChecked(),
                                     ui.ignoreBadPixelsCheckBox.isChecked(), ui.ignoreSaturatedPixelsCheckBox.isChecked(), ui.ignoreNonResponsivePixelsCheckBox.isChecked(), ui.ignoreConstantPixelsCheckBox.isChecked(),
                                     ui.signalBinsSpinBox.value(), ui.signalMinSpinBox.value(), ui.signalMaxSpinBox.value(),
                                     ui.noiseBinsSpinBox.value(), ui.noiseMinSpinBox.value(), ui.noiseMaxSpinBox.value(),
                                     ui.imagesToProcessSpinBox.value())
            ui.worker.image_count.connect(lambda progress, status: updateProgressDialogProgress(ui, progress, status))
            ui.worker.message.connect(lambda messsage, status: updateProgressDialogText(ui, messsage, status))
            ui.worker.started.connect(ui.progressDialog.show)
            ui.worker.finished.connect(ui.progressDialog.close)
            ui.progressDialog.canceled.connect(lambda: stopThread(ui))
            ui.worker.start()

        elif ui.pixelMaskFilePath_2.text() != '':
            dialog.messageCritical(ui, 'Error!', 'Please specify a bad-pixel map.')
        
        elif not os.path.exists(ui.pixelMaskFilePath_2.text()):
            dialog.messageCritical(ui, 'Error!', 'The currently selected Bad Pixel Map does not exist!\n\nSelect a Bad Pixel Map before continuing.')  
    
    elif ui.radiometryInputDirPath.text() == '':
        dialog.messageCritical(ui, 'Error!', 'Please specify an input directory.')
    
    elif not os.path.isdir(ui.radiometryInputDirPath.text()):
        dialog.messageCritical(ui, 'Error!', 'The current Radiometry Input Path does not exist!\n\nPlease select a directory that exists.')