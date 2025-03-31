# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from Tools.Settings import Settings

import MISC.dialog_boxes as dialog
import UI_Classes.Calibration_Widget as Calibration_Widget

#Function to perform image calibration
def Calibrate_Apply(ui):
    calibrateDialog = Calibration_Widget.Ui_Apply()
    if calibrateDialog.exec_():
        if calibrateDialog.inputDir != '' and calibrateDialog.outputDir != '' and calibrateDialog.calibrationFile != '':

            settings = Settings()
            settings.add_section_safely('calibration_apply')
            settings.set('calibration_apply', 'input_dir', calibrateDialog.inputDir)
            settings.set('calibration_apply', 'output_dir', calibrateDialog.outputDir)
            settings.set('calibration_apply', 'calibration_file', calibrateDialog.calibrationFile)
            settings.save()

            input_folder = calibrateDialog.inputDir
            output_folder = calibrateDialog.outputDir
            calib_file = calibrateDialog.calibrationFile

            ui = Calibration_Widget.UI_Apply_RUN(input_folder, output_folder, calib_file)
            ui.exec()

        else:
            dialog.messageWarning('Warning', 'Not all input has been provided, please try again.')


#Function to perform image calibration
def Calibrate_Create(ui):
    calibrateDialog = Calibration_Widget.Ui_Create_Setup()
    if calibrateDialog.exec_():
        if calibrateDialog.inputDir != '':
            settings = Settings()
            settings.add_section_safely('calibration_create')
            settings.set('calibration_create', 'input_dir', calibrateDialog.inputDir)
            settings.save()

            input_folder = calibrateDialog.inputDir
            tif_count = calibrateDialog.tif_count

            ui = Calibration_Widget.UI_Create_RUN(input_folder, tif_count)
            ui.exec()

        else:
            dialog.messageWarning('Warning', 'The directory has not been selected, please try again.')