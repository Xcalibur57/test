# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 20:08:40 2022

@author: mgoddard
"""

from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QProcess
from PyQt5 import uic

import os
from Tools.Settings import Settings
import MISC.dialog_boxes as dialog

#Class for the Calibration Widget, which allows users to input several paths as part of the calibration sequence
class Ui_Apply(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        uic.loadUi('UI/Calibration_Apply.ui', self)
        
        self.setWindowTitle('Apply NTC Calibration File')
        self.setWindowIcon(QIcon('_icons/MainWindow.png'))

        settings = Settings() 
        try:
            temp_inputDir = settings.get('calibration_apply', 'input_dir')
            temp_outputDir = settings.get('calibration_apply', 'output_dir')
            temp_calibrationFile = settings.get('calibration_apply', 'calibration_file')
        except:
            temp_inputDir = ''
            temp_outputDir = ''
            temp_calibrationFile = ''

        self.checkInputDirectory(temp_inputDir)
        self.checkOutputDirectory(temp_outputDir)
        self.checkCalibrationFile(temp_calibrationFile)
        
        self.selectInputDirButton.clicked.connect(self.selectInputDirectory)
        self.selectOutputDirButton.clicked.connect(self.selectOutputDirectory)
        self.selectCalibrationFileButton.clicked.connect(self.selectCalibrationFile)

    def checkInputDirectory(self, directory):
        if directory != '':
            self.inputDir = directory
            self.inputDirPath.setText(self.inputDir)

    def checkOutputDirectory(self, directory):
        if directory != '':
            self.outputDir = directory
            self.outputDirPath.setText(self.outputDir)

    def checkCalibrationFile(self, path):
        if path != '':
            self.calibrationFile = path
            self.calibrationFilePath.setText(self.calibrationFile)

    def selectInputDirectory(self):
        temp_inputDir = QFileDialog.getExistingDirectory(self, "Select Raw Image Directory")
        self.checkInputDirectory(temp_inputDir)
        

    def selectOutputDirectory(self):
        temp_outputDir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        self.checkOutputDirectory(temp_outputDir)
        
        
    def selectCalibrationFile(self):
        temp_calibrationFile = QFileDialog.getOpenFileName(self, 'Select NTC File', self.calibrationFile, 'Calibration files (*.ntc)')[0]
        self.checkCalibrationFile(temp_calibrationFile)

# Class for the GUI to interact with the called program to generate a calibration file.
class UI_Apply_RUN(QDialog):
    def __init__(self, input_folder, output_folder, calib_file):
        QDialog.__init__(self)
        uic.loadUi('UI/Calibration_Apply_RUN.ui', self)
        
        self.setWindowTitle('Apply NTC Calibration File')
        self.setWindowIcon(QIcon('_icons/MainWindow.png'))

        self.input_folder = input_folder
        self.output_folder = output_folder
        self.ntc_file = calib_file

        self.checkInputFolder()
        self.checkOutputFolder()

        self.progressBar.setValue(0)

        self.runButton.clicked.connect(self.callProgram)
        self.cancelButton.clicked.connect(self.killProcess)
        
        self.process = QProcess(self)
        self.process.readyRead.connect(self.dataReady)
        self.process.started.connect(lambda: self.runButton.setEnabled(False))
        self.process.started.connect(lambda: self.cancelButton.setEnabled(True))
        self.process.finished.connect(lambda: self.runButton.setEnabled(True))
        self.process.finished.connect(lambda: self.cancelButton.setEnabled(False))
        self.process.finished.connect(self.checkForNextRun)

    def checkInputFolder(self):
        self.isSingleFolder = False
        self.temp_num_sub_folders = 0
        self.temp_num_images_total = 0
        self.other_count = 0
        self.input_folders = []

        for item in os.listdir(self.input_folder):
            if os.path.isdir(os.path.join(self.input_folder, item)):
                self.temp_num_sub_folders += 1
                for image in os.listdir(os.path.join(self.input_folder, item)):
                    if image.endswith('.tif'):
                        self.temp_num_images_total += 1
                    else:
                        self.other_count += 1
            else:
                self.isSingleFolder = True
                if item.endswith('.tif'):
                    self.temp_num_images_total += 1
                else:
                    self.other_count += 1

        self.numImagesLabel.setText(str(self.temp_num_images_total))
        self.numFoldersLabel.setText(str(self.temp_num_sub_folders))

    def checkOutputFolder(self):
        if os.path.exists(self.output_folder):
            if self.isSingleFolder:
                temp_image_count = 0
                for item in os.listdir(self.output_folder):
                    if item.endswith('.tif'):
                        temp_image_count += 1
                if temp_image_count > 0:
                    dialog.messageInformation(self, 'Take Note!', 'The output folder selected already contains images - these will be overwritten when generating new calibrated images.\n\nIf you wish to retain these images, move them to a different directory before clicking \'Run\' on the next window.')
            else:
                temp_image_count = 0
                for folder in os.listdir(self.output_folder):
                    if os.path.exists(os.path.join(self.output_folder, folder)):
                        if os.path.isdir(os.path.join(self.output_folder, folder)):
                            for image in os.listdir(os.path.join(self.output_folder, folder)):
                                if image.endswith('.tif'):
                                    temp_image_count += 1
                if temp_image_count > 0:
                    dialog.messageInformation(self, 'Take Note!', 'The output folder contains folders which already contain images - these will be overwritten when generating new calibrated images.\n\nIf you wish to retain these images, move them to a different directory before clicking \'Run\' on the next window.')


    def dataReady(self):
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.End)
        text = str(self.process.readAll(), encoding='utf-8')
        cursor.insertText(text)    
        if 'SvuNtcApply' not in text and 'Compiled' not in text:
            self.num_images_processed += 1
            progress = int(100 * self.num_images_processed / self.temp_num_images_total)
            self.progressBar.setValue(progress)
            if progress == 100:
                cursor.insertText('Done!\n\nClose window to continue.')
        self.output.ensureCursorVisible()

    def checkForNextRun(self):
        if not self.isSingleFolder:
            if self.processed_folders < self.temp_num_sub_folders:
                file = open(self.filename, 'w')
                file.writelines("# SVuNtcApplySettings \n")
                file.writelines("version=1 \n")
                file.writelines("# The calibration to be applied to images.\n")
                file.writelines("""calibration = "{}"\n""".format(self.ntc_file))
                file.writelines("# Folder containing the input images.\n")
                file.writelines("""image_folder="{}"\n""".format(os.path.join(self.input_folder, self.input_folders[self.processed_folders])))
                file.writelines("# Folder where the corrected images will be stored.\n")
                file.writelines("""output_folder="{}"\n""".format(os.path.join(self.output_folder, self.input_folders[self.processed_folders])))

                for item in os.listdir(os.path.join(self.input_folder, self.input_folders[self.processed_folders])):
                    if item.endswith('.tif'):
                        file.writelines("image={}\n".format(item))
                file.close()

                self.process.start("Calibration/SvuNtcApply.exe", [self.filename])
                self.processed_folders += 1

    def callProgram(self):
        self.filename = "Calibration/images_to_process.txt"
        self.progressBar.setValue(0)
        self.num_images_processed = 0

        if self.isSingleFolder:
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            file = open(self.filename, 'w')
            file.writelines("# SVuNtcApplySettings \n")
            file.writelines("version=1 \n")
            file.writelines("# The calibration to be applied to images.\n")
            file.writelines("""calibration = "{}"\n""".format(self.ntc_file))
            file.writelines("# Folder containing the input images.\n")
            file.writelines("""image_folder="{}"\n""".format(self.input_folder))
            file.writelines("# Folder where the corrected images will be stored.\n")
            file.writelines("""output_folder="{}"\n""".format(self.output_folder))
            
            for item in os.listdir(self.input_folder):
                if item.endswith('.tif'):
                   file.writelines("image={}\n".format(item))
            file.close()

            self.process.start("Calibration/SvuNtcApply.exe", [self.filename])
        else:
            for item in os.listdir(self.input_folder):
                if os.path.isdir(os.path.join(self.input_folder, item)):
                    if not os.path.exists(os.path.join(self.output_folder, item)):
                        os.makedirs(os.path.join(self.output_folder, item))
                    self.input_folders.append(item)
            
            self.processed_folders = 0
            self.checkForNextRun()

    def killProcess(self):
        try:
            self.process.kill()
            self.progressBar.setValue(0)
            self.runButton.setEnabled(True)
            self.cancelButton.setEnabled(False)

            cursor = self.output.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertText('Operation cancelled!\n')
        except:
            dialog.messageCritical(self, 'Critical Error', 'Something went wrong, and could not cancel the operation.\n\nError code: E1082')

#Class for the Calibration Widget, which allows users to input several paths as part of the calibration sequence
class Ui_Create_Setup(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        uic.loadUi('UI/Calibration_Create_Setup.ui', self)
        
        self.setWindowTitle('Create NTC Calibration File')
        self.setWindowIcon(QIcon('_icons/MainWindow.png'))

        settings = Settings() 
        try:
            temp_inputDir = settings.get('calibration_create', 'input_dir')
        except:
            temp_inputDir = ''
        
        self.checkDirectory(temp_inputDir)
        self.selectInputDirButton.clicked.connect(self.selectInputDirectory)

    def checkDirectory(self, temp_inputDir):
        if temp_inputDir != '' and os.path.isdir(temp_inputDir):
            subfolder_count = 0
            self.tif_count = 0
            ntc_count = 0
            other_count = 0

            for item in os.listdir(temp_inputDir):
                if os.path.isdir(os.path.join(temp_inputDir,item)):
                    subfolder_count += 1
                elif os.path.join(temp_inputDir, item).endswith('.tif'):
                    self.tif_count += 1
                elif os.path.join(temp_inputDir, item).endswith('.ntc'):
                    ntc_count += 1
                else:
                    other_count += 1
            
            if subfolder_count != 0:
                dialog.messageCritical(self, 'Error', 'The folder you selected contains subfolders! \n\nPlease remove all subfolders from the directory containing calibration data files.\n\nError code: E1083')
            else:
                if self.tif_count <= 10:
                    dialog.messageCritical(self, 'Error', 'The folder you selected does not contain enough .tif files! \n\nPlease select a directory which contains enough files to generate a calibration.\n\nError code: E1084')
                else:
                    if ntc_count > 0:
                        dialog.messageWarning(self, 'Warning', 'The folder you selected already contains an .ntc file! \n\nThis file will be overwritten.')
                    if other_count > 0:
                        dialog.messageWarning(self, 'Warning', 'The folder you selected contains items other than .tif or .ntc files! \n\nThese files will be ignored.')
                    
                    self.inputDir = temp_inputDir
                    self.inputDirPath.setText(self.inputDir)
        elif not os.path.isdir(temp_inputDir):
            dialog.messageWarning(self, 'Warning', 'The folder loaded from settings.ini does not exist! \n\nPlease select a valid directory.')

    def selectInputDirectory(self):
        temp_inputDir = QFileDialog.getExistingDirectory(self, "Select Raw Ramp Image Directory")
        self.checkDirectory(temp_inputDir)

# Class for the GUI to interact with the called program to generate a calibration file.
class UI_Create_RUN(QDialog):
    def __init__(self, input_folder, tif_count):
        # super(UI_Create_RUN, self).__init__()
        QDialog.__init__(self)
        uic.loadUi('UI/Calibration_Create_RUN.ui', self)
        
        self.setWindowTitle('Create NTC Calibration File')
        self.setWindowIcon(QIcon('_icons/MainWindow.png'))

        self.input_folder = input_folder
        self.numImagesLabel.setText(str(tif_count))
        self.runButton.clicked.connect(self.callProgram)

        self.progressBar.setValue(0)

        self.process = QProcess(self)
        self.process.readyRead.connect(self.dataReady)
        self.process.started.connect(lambda: self.runButton.setEnabled(False))
        self.process.started.connect(lambda: self.cancelButton.setEnabled(True))
        self.process.finished.connect(lambda: self.runButton.setEnabled(True))
        self.process.finished.connect(lambda: self.cancelButton.setEnabled(False))
        self.cancelButton.clicked.connect(self.killProcess)

    def dataReady(self):
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.End)
        text = str(self.process.readAll(), encoding='utf-8')
        cursor.insertText(text)
        if 'First estimate of statistics.' in text:
            self.progressBar.setValue(10)
            cursor.insertText('Please wait...\n')
        elif 'Second estimate of statistics.' in text:
            self.progressBar.setValue(55)
            cursor.insertText('Please wait...\n')
        elif 'Pixels with no gain and offset' in text:
            cursor.insertText('Done!\n\nClose window to continue.')
            self.progressBar.setValue(100)
        
        self.output.ensureCursorVisible()

    def callProgram(self):
        self.process.start("Calibration/SvuNtcCreate.exe", [self.input_folder])
        if self.process.state() == 0:
            dialog.messageCritical(self, 'Critical Error', 'Something went wrong, and could not start the operation. Check that the file \'SvuNtcCreate.exe\' exists.\n\nError code: E1085')
        else:
            self.progressBar.setValue(5)


    def killProcess(self):
        try:
            self.process.kill()
            self.progressBar.setValue(0)
            self.runButton.setEnabled(True)
            self.cancelButton.setEnabled(False)

            cursor = self.output.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertText('Operation cancelled!\n')
        except:
            dialog.messageCritical(self, 'Critical Error', 'Something went wrong, and could not cancel the operation.\n\nError code: E1086')