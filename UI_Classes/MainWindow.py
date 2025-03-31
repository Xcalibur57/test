# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 12:48:49 2022

@author: mgoddard
"""

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtGui import QImage, QIcon
from Tools.Settings import Settings

import numpy as np
import os

import Radiometry.Radiometry_Process as Radiometry_Process
import Calibration.Calibration_Process as Calibration_Process
import ThroughFocus.Through_Focus as Through_Focus
import Tools.video_process as video_process
import Tools.wholenineyards_process as wholenineyards_process
import Tools.prettify_process as prettify_process

import Help.Help_Process as Help
import MISC.dialog_boxes as dialog
import MTF.MTF_Functions as MTF_Functions

class Ui(QMainWindow):

    def __init__(self):
        '''
        Initialisation function for the custom class UI(QMainWindow) MainWindow. 
        
        Sets up application housekeeping, and makes all signal/slot connections required for application startup.
        '''
        
        super(Ui, self).__init__()
        uic.loadUi('UI/MainWindow.ui', self)
        
        # Housekeeping
        version = 'v0.57, 28/03/2025 MKG'
        title = "SSTL - DarkCarb Image Processing Software"
        self.setWindowTitle(str(title + ' - ' + version))
        self.setWindowIcon(QIcon('_icons/MainWindow.png'))

        self.settingsLoad()
        self.makeConnections()

        self.singleMat = np.float64([])    # used for real processing
        self.singleImage = QImage()      # Used for diaplay purposes only
        
        self.show()

    def makeConnections(self):
        """
        Initialise the connections between signals and slots for the main window ui.
        """

        # Application start house-keeping
        self.mtfTabWidget.setCurrentIndex(0)
        self.statusbar.showMessage('Load an image, or image stack')
        self.MtfFrequency.addItems(['Half-Nyquist', 'Nyquist'])
        self.MtfFrequency.setCurrentIndex(1)

        # Application Startup connections
        # Through Focus Buttons
        self.selectTFInputDirPushButton.clicked.connect(lambda: Through_Focus.SelectInputDirectory(self))
        self.GenerateCSVpushButton.clicked.connect(lambda: Through_Focus.GenerateEdgeCSV(self))
        self.processCSVpushButton.clicked.connect(lambda: Through_Focus.ProcessEdgeCSV(self))

        # Radiometry Buttons
        self.radiometryPushButton.clicked.connect(lambda: Radiometry_Process.RadiometryWorkerStart(self))

        # Load Image Buttons
        self.loadImageButton.clicked.connect(lambda: MTF_Functions.loadImage(self))                    # Load Image Button
        self.loadImageAverageMtf.clicked.connect(lambda: MTF_Functions.BulkAnalyseAndAverage(self))    # Load Image (Average MTF) Button
        self.loadImageStackButton.clicked.connect(lambda: MTF_Functions.AnalyseStack(self))            # Load Image Stack Button
        # Image Setup Page Buttons
        self.defineAoiButton.clicked.connect(lambda: MTF_Functions.defineAoi(self))                    # AOI Selection Button
        self.findEdgeButton.clicked.connect(lambda: MTF_Functions.findEdge(self))                      # Find Edge Button
        self.analyseButton.clicked.connect(lambda: MTF_Functions.analyse(self))                        # Analyse Button
        # Analysis Page Buttons
        self.getNewEdgeData.clicked.connect(lambda: MTF_Functions.analyse(self))                       # Get New Edge Data Button
        self.fitEsfCurve.clicked.connect(lambda: MTF_Functions.fitESFCurve(self))                      # Fit Curve Button

        # Image Processing Buttons
        self.selectPixelMaskFileButton.clicked.connect(self.selectBadPixelMask)
        
        self.selectVideoInputDirButton.clicked.connect(self.selectVideoInputPath)
        self.selectPrettifyInputDirButton.clicked.connect(self.selectPrettifyInputPath)
        self.selectPrettifyOutputDirButton.clicked.connect(self.selectPrettifyOutputPath)
        self.selectWNYInputDirButton.clicked.connect(self.selectWNYInputPath)
        self.selectNUCFileButton.clicked.connect(self.selectNUCFile)

        self.videoButtonBox.accepted.connect(lambda: video_process.Video(self))
        self.prettifyButtonBox.accepted.connect(lambda: prettify_process.Prettify(self))
        self.WNYButtonBox.accepted.connect(lambda: wholenineyards_process.WholeNineYards(self))

        # Radiometry Buttons
        self.selectPixelMaskFileButton_2.clicked.connect(self.selectBadPixelMask)
        self.selectRadiometryInputDirButton.clicked.connect(self.selectRadiometryInputPath)

        # Values Change
        self.aoiSize.valueChanged.connect(lambda: MTF_Functions.drawAoi(self))                         
        self.MtfFrequency.currentIndexChanged.connect(lambda: MTF_Functions.MTFCurve(self))
        self.lengthOfEdgeLine.valueChanged.connect(lambda: MTF_Functions.updateAoiImage(self))
        self.normalDistanceFromEdge.valueChanged.connect(lambda: MTF_Functions.updateAoiImage(self))

        # Actions
        self.actionSave_Settings.triggered.connect(self.settingsSave)                       # Save Settings
        self.actionLoad_Settings.triggered.connect(self.settingsLoad)

        self.actionCalibrate_Images_Apply.triggered.connect(Calibration_Process.Calibrate_Apply)
        self.actionCalibrate_Images_Create.triggered.connect(Calibration_Process.Calibrate_Create)
        self.actionGetting_Started_Window.triggered.connect(Help.GettingStarted)


    def settingsLoad(self):
        '''
        Loads the settings for the application from the 'settings.ini' file in the application root directory.
        '''
           
        settings = Settings()

        try:    
            self.removeExtraPixelsCheckBox.setChecked(settings.getboolean('image_setup', 'remove_ancilliary_data'))
            self.convertTo16BitsCheckBox.setChecked(settings.getboolean('image_setup', 'convert_to_16_bits'))
            self.aoiSize.setValue(settings.getint('image_setup', 'aoi_size'))
            self.removeDeadPixels.setChecked(settings.getboolean('image_setup', 'bad_pixel_remove'))
            self.badPixelFactorSpinBox.setValue(settings.getfloat('image_setup', 'bad_pixel_factor'))
            self.dynamicAoi.setChecked(settings.getboolean('image_setup', 'dynamic_aoi'))
            self.pixelSize.setValue(settings.getfloat('image_setup', 'pixel_size'))
        except:
            dialog.messageCritical(self, 'Error', 'Failed to load \'image_setup\' settings!')

        try:
            self.normalDistanceFromEdge.setValue(settings.getint('analysis', 'normal_distance_to_edge'))
            self.lengthOfEdgeLine.setValue(settings.getint('analysis', 'length_of_edge'))
            self.removeNoise.setChecked(settings.getboolean('analysis', 'remove_noise'))
            self.sigmaScalingSpinBox.setValue(settings.getfloat('analysis', 'sigma_scaling_factor'))
            self.smoothingAlpha.setValue(settings.getfloat('analysis', 'smoothing_alpha'))
            self.oversamplingMultiplier.setValue(settings.getint('analysis', 'oversampling_per_pixel'))
            self.tailSmoothing.setChecked(settings.getboolean('analysis', 'tail_smoothing'))
            self.tailStartdT.setValue(settings.getfloat('analysis', 'tail_scale'))
            self.tailSmoothSpinBox.setValue(settings.getfloat('analysis', 'tail_smoothing_width'))
        except:
            dialog.messageCritical(self, 'Error', 'Failed to load \'analysis\' settings!')

        try:
            self.radiometryInputDirPath.setText(settings.get('radiometry', 'radiometry_input_dir'))
            self.radiometrySaveCSVFileCheckBox.setChecked(settings.getboolean('radiometry', 'save_csv_file'))
            self.radiometrySavePlotsCheckBox.setChecked(settings.getboolean('radiometry', 'save_plots'))
            self.radiometryDisplayPlotsCheckBox.setChecked(settings.getboolean('radiometry', 'display_plots'))
            self.averagingMeanCheckBox.setChecked(settings.getboolean('radiometry', 'averaging_mean'))
            self.averagingMedianCheckBox.setChecked(settings.getboolean('radiometry', 'averaging_median'))
            self.averagingModeCheckBox.setChecked(settings.getboolean('radiometry', 'averaging_mode'))
            self.ignoreBadPixelsCheckBox.setChecked(settings.getboolean('radiometry', 'ignore_px_bad'))
            self.ignoreSaturatedPixelsCheckBox.setChecked(settings.getboolean('radiometry', 'ignore_px_saturated'))
            self.ignoreNonResponsivePixelsCheckBox.setChecked(settings.getboolean('radiometry', 'ignore_px_non_responsive'))
            self.ignoreConstantPixelsCheckBox.setChecked(settings.getboolean('radiometry', 'ignore_px_constant'))
            self.signalBinsSpinBox.setValue(settings.getint('radiometry', 'signal_bins'))
            self.signalMinSpinBox.setValue(settings.getint('radiometry', 'signal_bins_min'))
            self.signalMaxSpinBox.setValue(settings.getint('radiometry', 'signal_bins_max'))
            self.noiseBinsSpinBox.setValue(settings.getint('radiometry', 'noise_bins'))
            self.noiseMinSpinBox.setValue(settings.getfloat('radiometry', 'noise_bins_min'))
            self.noiseMaxSpinBox.setValue(settings.getint('radiometry', 'noise_bins_max'))
            self.imagesToProcessSpinBox.setValue(settings.getint('radiometry', 'images_to_process'))
        except:
            dialog.messageCritical(self, 'Error', 'Failed to load \'radiometry\' settings!')

        try:
            self.pixelMaskFilePath.setText(settings.get('image_processing', 'bad_pixel_mask_path'))
            self.pixelMaskFilePath_2.setText(settings.get('image_processing', 'bad_pixel_mask_path'))
            self.videoInputDirPath.setText(settings.get('image_processing', 'video_input_dir'))
            self.prettifyInputDirPath.setText(settings.get('image_processing', 'prettify_input_dir'))
            self.prettifyOutputDirPath.setText(settings.get('image_processing', 'prettify_output_dir'))
            self.WNYInputDirPath.setText(settings.get('image_processing', 'wny_input_dir'))
            self.NUCFilePath.setText(settings.get('image_processing', 'nuc_file'))

            self.checkBoxAppendAncillaryData.setChecked(settings.getboolean('image_processing', 'append_ancillary_data'))
            self.checkBoxAutofillBadPixels.setChecked(settings.getboolean('image_processing', 'autofil_bad_pixels'))
            self.checkBoxAutoscaleDynamicRange.setChecked(settings.getboolean('image_processing', 'autoscale_dynamic_range'))
            self.checkBoxDespeckle.setChecked(settings.getboolean('image_processing', 'despeckle'))
            self.checkBoxInvertImageData.setChecked(settings.getboolean('image_processing', 'invert'))
            self.checkBoxFlipHorizontal.setChecked(settings.getboolean('image_processing', 'flip'))

            self.checkBoxColormapJet.setChecked(settings.getboolean('image_processing', 'jet'))
            self.checkBoxHSV.setChecked(settings.getboolean('image_processing', 'hsv'))
            self.checkBoxInferno.setChecked(settings.getboolean('image_processing', 'inferno'))
            self.checkBoxRainbow.setChecked(settings.getboolean('image_processing', 'rainbow'))
            self.checkBoxHot.setChecked(settings.getboolean('image_processing', 'hot'))
            self.checkBoxOcean.setChecked(settings.getboolean('image_processing', 'ocean'))
            self.checkBoxViridis.setChecked(settings.getboolean('image_processing', 'viridis'))
            self.checkBoxTwilightShifted.setChecked(settings.getboolean('image_processing', 'twilight'))

            self.checkBoxAppendAncillaryData_2.setChecked(settings.getboolean('image_processing', 'append_ancillary_data_2'))
            self.checkBoxAutofillBadPixels_2.setChecked(settings.getboolean('image_processing', 'autofil_bad_pixels_2'))
            self.checkBoxAutoscaleDynamicRange_2.setChecked(settings.getboolean('image_processing', 'autoscale_dynamic_range_2'))
            self.checkBoxDespeckle_2.setChecked(settings.getboolean('image_processing', 'despeckle_2'))
            self.checkBoxInvertImageData_2.setChecked(settings.getboolean('image_processing', 'invert_2'))
            self.checkBoxFlipHorizontal_2.setChecked(settings.getboolean('image_processing', 'flip_2'))
            self.checkBoxRawWithoutAncil.setChecked(settings.getboolean('image_processing', 'raw_without_ancillary'))
            self.checkBoxNUCWithAncil.setChecked(settings.getboolean('image_processing', 'nuc_with_ancillary'))
            self.checkBoxSaveBadPixel.setChecked(settings.getboolean('image_processing', 'save_bad_pixel'))
            self.checkBoxSaveInverted.setChecked(settings.getboolean('image_processing', 'save_invert'))
            self.checkBoxSaveDespeckled.setChecked(settings.getboolean('image_processing', 'save_despeckle'))

            self.checkBoxColormapJet_2.setChecked(settings.getboolean('image_processing', 'jet_2'))
            self.checkBoxHSV_2.setChecked(settings.getboolean('image_processing', 'hsv_2'))
            self.checkBoxInferno_2.setChecked(settings.getboolean('image_processing', 'inferno_2'))
            self.checkBoxRainbow_2.setChecked(settings.getboolean('image_processing', 'rainbow_2'))
            self.checkBoxHot_2.setChecked(settings.getboolean('image_processing', 'hot_2'))
            self.checkBoxOcean_2.setChecked(settings.getboolean('image_processing', 'ocean_2'))
            self.checkBoxViridis_2.setChecked(settings.getboolean('image_processing', 'viridis_2'))
            self.checkBoxTwilightShifted_2.setChecked(settings.getboolean('image_processing', 'twilight_2'))
        except:
            dialog.messageCritical(self, 'Error', 'Failed to load \'image_processing\' settings!')

        try:
            self.topLevelTabWidget.setCurrentIndex(settings.getint('application', 'top_level_tab'))

            if settings.getboolean('application', 'is_maximized'):
                self.showMaximized()
            else:
                x = settings.getint('application', 'window_xpos')
                y = settings.getint('application', 'window_ypos')
                w = settings.getint('application', 'window_width')
                h = settings.getint('application', 'window_height')

                self.setGeometry(x+1, y+31, w, h)
        except:
            dialog.messageCritical(self, 'Error', 'Failed to load \'application\' settings!')

    def settingsSave(self):
        '''
        Saves the settings for the application to the 'settings.ini' file in the application root directory.
        '''

        settings = Settings()

        settings.add_section_safely('image_setup')
        settings.set('image_setup', 'remove_ancilliary_data', str(self.removeExtraPixelsCheckBox.isChecked()))
        settings.set('image_setup', 'convert_to_16_bits', str(self.convertTo16BitsCheckBox.isChecked()))
        settings.set('image_setup', 'aoi_size', str(self.aoiSize.value()))
        settings.set('image_setup', 'bad_pixel_remove', str(self.removeDeadPixels.isChecked()))
        settings.set('image_setup', 'bad_pixel_factor', str(self.badPixelFactorSpinBox.value()))
        settings.set('image_setup', 'dynamic_aoi', str(self.dynamicAoi.isChecked()))
        settings.set('image_setup', 'pixel_size', str(self.pixelSize.value()))

        settings.add_section_safely('analysis')
        settings.set('analysis', 'normal_distance_to_edge', str(self.normalDistanceFromEdge.value()))
        settings.set('analysis', 'length_of_edge', str(self.lengthOfEdgeLine.value()))
        settings.set('analysis', 'remove_noise', str(self.removeNoise.isChecked()))
        settings.set('analysis', 'sigma_scaling_factor', str(self.sigmaScalingSpinBox.value()))
        settings.set('analysis', 'smoothing_alpha', str(self.smoothingAlpha.value()))
        settings.set('analysis', 'oversampling_per_pixel', str(self.oversamplingMultiplier.value()))
        settings.set('analysis', 'tail_smoothing', str(self.tailSmoothing.isChecked()))
        settings.set('analysis', 'tail_scale', str(self.tailStartdT.value()))
        settings.set('analysis', 'tail_smoothing_width', str(self.tailSmoothSpinBox.value()))
        settings.set('analysis', 'nyquist', str(self.MtfFrequency.currentText()))

        settings.add_section_safely('radiometry')
        settings.set('radiometry', 'radiometry_input_dir', str(self.radiometryInputDirPath.text()))
        settings.set('radiometry', 'save_csv_file', str(self.radiometrySaveCSVFileCheckBox.isChecked()))
        settings.set('radiometry', 'save_plots', str(self.radiometrySavePlotsCheckBox.isChecked()))
        settings.set('radiometry', 'display_plots', str(self.radiometryDisplayPlotsCheckBox.isChecked()))
        settings.set('radiometry', 'averaging_mean', str(self.averagingMeanCheckBox.isChecked()))
        settings.set('radiometry', 'averaging_median', str(self.averagingMedianCheckBox.isChecked()))
        settings.set('radiometry', 'averaging_mode', str(self.averagingModeCheckBox.isChecked()))
        settings.set('radiometry', 'ignore_px_bad', str(self.ignoreBadPixelsCheckBox.isChecked()))
        settings.set('radiometry', 'ignore_px_saturated', str(self.ignoreSaturatedPixelsCheckBox.isChecked()))
        settings.set('radiometry', 'ignore_px_non_responsive', str(self.ignoreNonResponsivePixelsCheckBox.isChecked()))
        settings.set('radiometry', 'ignore_px_constant', str(self.ignoreConstantPixelsCheckBox.isChecked()))
        settings.set('radiometry', 'signal_bins', str(self.signalBinsSpinBox.value()))
        settings.set('radiometry', 'signal_bins_min', str(self.signalMinSpinBox.value()))
        settings.set('radiometry', 'signal_bins_max', str(self.signalMaxSpinBox.value()))
        settings.set('radiometry', 'noise_bins', str(self.noiseBinsSpinBox.value()))
        settings.set('radiometry', 'noise_bins_min', str(self.noiseMinSpinBox.value()))
        settings.set('radiometry', 'noise_bins_max', str(self.noiseMaxSpinBox.value()))
        settings.set('radiometry', 'images_to_process', str(self.imagesToProcessSpinBox.value()))

        settings.add_section_safely('image_processing')
        settings.set('image_processing', 'bad_pixel_mask_path', str(self.pixelMaskFilePath.text()))
        settings.set('image_processing', 'video_input_dir', str(self.videoInputDirPath.text()))
        settings.set('image_processing', 'prettify_input_dir', str(self.prettifyInputDirPath.text()))
        settings.set('image_processing', 'prettify_output_dir', str(self.prettifyOutputDirPath.text()))
        settings.set('image_processing', 'wny_input_dir', str(self.WNYInputDirPath.text()))
        settings.set('image_processing', 'nuc_file', str(self.NUCFilePath.text()))

        settings.set('image_processing', 'append_ancillary_data', str(self.checkBoxAppendAncillaryData.isChecked()))
        settings.set('image_processing', 'autofil_bad_pixels', str(self.checkBoxAutofillBadPixels.isChecked()))
        settings.set('image_processing', 'autoscale_dynamic_range', str(self.checkBoxAutoscaleDynamicRange.isChecked()))
        settings.set('image_processing', 'despeckle', str(self.checkBoxDespeckle.isChecked()))
        settings.set('image_processing', 'invert', str(self.checkBoxInvertImageData.isChecked()))
        settings.set('image_processing', 'flip', str(self.checkBoxFlipHorizontal.isChecked()))

        settings.set('image_processing', 'jet', str(self.checkBoxColormapJet.isChecked()))
        settings.set('image_processing', 'hsv', str(self.checkBoxHSV.isChecked()))
        settings.set('image_processing', 'inferno', str(self.checkBoxInferno.isChecked()))
        settings.set('image_processing', 'rainbow', str(self.checkBoxRainbow.isChecked()))
        settings.set('image_processing', 'hot', str(self.checkBoxHot.isChecked()))
        settings.set('image_processing', 'ocean', str(self.checkBoxOcean.isChecked()))
        settings.set('image_processing', 'viridis', str(self.checkBoxViridis.isChecked()))
        settings.set('image_processing', 'twilight', str(self.checkBoxTwilightShifted.isChecked()))

        settings.set('image_processing', 'append_ancillary_data_2', str(self.checkBoxAppendAncillaryData_2.isChecked()))
        settings.set('image_processing', 'autofil_bad_pixels_2', str(self.checkBoxAutofillBadPixels_2.isChecked()))
        settings.set('image_processing', 'autoscale_dynamic_range_2', str(self.checkBoxAutoscaleDynamicRange_2.isChecked()))
        settings.set('image_processing', 'despeckle_2', str(self.checkBoxDespeckle_2.isChecked()))
        settings.set('image_processing', 'invert_2', str(self.checkBoxInvertImageData_2.isChecked()))
        settings.set('image_processing', 'flip_2', str(self.checkBoxFlipHorizontal_2.isChecked()))
        settings.set('image_processing', 'raw_without_ancillary', str(self.checkBoxRawWithoutAncil.isChecked()))
        settings.set('image_processing', 'nuc_with_ancillary', str(self.checkBoxNUCWithAncil.isChecked()))
        settings.set('image_processing', 'save_bad_pixel', str(self.checkBoxSaveBadPixel.isChecked()))
        settings.set('image_processing', 'save_invert', str(self.checkBoxSaveInverted.isChecked()))
        settings.set('image_processing', 'save_despeckle', str(self.checkBoxSaveDespeckled.isChecked()))

        settings.set('image_processing', 'jet_2', str(self.checkBoxColormapJet_2.isChecked()))
        settings.set('image_processing', 'hsv_2', str(self.checkBoxHSV_2.isChecked()))
        settings.set('image_processing', 'inferno_2', str(self.checkBoxInferno_2.isChecked()))
        settings.set('image_processing', 'rainbow_2', str(self.checkBoxRainbow_2.isChecked()))
        settings.set('image_processing', 'hot_2', str(self.checkBoxHot_2.isChecked()))
        settings.set('image_processing', 'ocean_2', str(self.checkBoxOcean_2.isChecked()))
        settings.set('image_processing', 'viridis_2', str(self.checkBoxViridis_2.isChecked()))
        settings.set('image_processing', 'twilight_2', str(self.checkBoxTwilightShifted_2.isChecked()))

        settings.add_section_safely('application')
        settings.set('application', 'top_level_tab', str(self.topLevelTabWidget.currentIndex()))
        settings.set('application', 'window_width', str(self.size().width()))
        settings.set('application', 'window_height', str(self.size().height()))
        settings.set('application', 'window_xpos', str(max(self.pos().x(), 0)))
        settings.set('application', 'window_ypos', str(max(self.pos().y(), 0)))
        settings.set('application', 'is_maximized', str(self.isMaximized())) 

        settings.save()


    def selectBadPixelMask(self):
        '''
        Opens a QFileDialog and allows the user to select the bad-pixel mask .csv file.
        Updates the UI with the selected path.
        '''

        path = self.pixelMaskFilePath.text()
        selectedPath = QFileDialog.getOpenFileName(self, 'Select Bad Pixel Mask', path, 'CSV (*.csv)')
        if selectedPath[0] != '':
            self.pixelMaskFilePath.setText(selectedPath[0])
            self.pixelMaskFilePath_2.setText(selectedPath[0])


    def selectVideoInputPath(self):
        '''
        Opens a QFileDialog and allows the user to select the input folder for video creation.
        Updates the UI with the selected path.
        '''
 
        path = self.videoInputDirPath.text()
        selectedDir = QFileDialog.getExistingDirectory(self, "Select a Directory", path)
        if selectedDir != '':
            self.videoInputDirPath.setText(selectedDir)


    def selectPrettifyInputPath(self):
        '''
        Opens a QFileDialog and allows the user to select the input folder for creating pretty images.
        Updates the UI with the selected path.
        '''

        path = self.prettifyInputDirPath.text()
        selectedDir = QFileDialog.getExistingDirectory(self, "Select a Directory", path)
        if selectedDir != '':
            self.prettifyInputDirPath.setText(selectedDir)
            self.prettifyOutputDirPath.setText(os.path.dirname(selectedDir))
 

    def selectPrettifyOutputPath(self):
        '''
        Opens a QFileDialog and allows the user to select the output folder for pretty images.
        Updates the UI with the selected path.
        '''

        path = self.prettifyOutputDirPath.text()
        selectedDir = QFileDialog.getExistingDirectory(self, "Select a Directory", path)
        if selectedDir != '':
            if selectedDir != os.path.dirname(self.prettifyInputDirPath.text()):
                dialog.messageWarning(self, 'Be Careful!', 'You have selected an output folder which is not the parent of the input folder, this may cause issues!')
            self.prettifyOutputDirPath.setText(selectedDir)


    def selectWNYInputPath(self):
        '''
        Opens a QFileDialog and allows the user to select the input folder for the Whole Nine Yards Process.
        Updates the UI with the selected path.
        '''

        path = self.WNYInputDirPath.text()
        selectedDir = QFileDialog.getExistingDirectory(self, "Select a Directory", path)
        if selectedDir != '':
            if selectedDir.endswith('01_raw_w_ancillary_data'):
                self.WNYInputDirPath.setText(selectedDir)
            else:
                dialog.messageCritical(self, 'Warning!', 'You have not selected a compatible folder, please select a folder which has the name \'01_raw_w_ancillary_data\'!')


    def selectNUCFile(self):
        '''
        Opens a QFileDialog and allows the user to select the NUC .ntc file to be used to calibrate images.
        Updates the UI with the selected path.
        '''

        path = self.NUCFilePath.text()
        selectedPath = QFileDialog.getOpenFileName(self, 'Select NUC File', path, 'NTC Files(*.ntc)')
        if selectedPath[0] != '':
            self.NUCFilePath.setText(selectedPath[0])

    def selectRadiometryInputPath(self):
        '''
        Opens a QFileDialog and allows the user to select the input folder for radiometry processing.
        Updates the UI with the selected path.
        '''

        # path = self.videoInputDirPath.text()
        # selectedDir = QFileDialog.getExistingDirectory(self, "Select a Directory", path)
        # if selectedDir != '':
        #     self.videoInputDirPath.setText(selectedDir)


        dialog.messageInformation(self, 'Take Note!', "Select a parent directory which contains folders of temperature values ending in either \'raw\' or \'calibrated\'.\n\nThe temperature folder must contain folders of the individual integration times, ending in \'ms\'.")

        path = self.radiometryInputDirPath.text()
        selectedDir = QFileDialog.getExistingDirectory(self, "Select a Directory", path)
        if selectedDir != '':
            self.radiometryInputDirPath.setText(selectedDir)


    def closeEvent(self, event):
        '''
        Handle a closure event for the 'MainWindow' UI Application.

        Parameters
        ----------
        self: Class
            Parent class for the closure event.
        event: Event
            Not Used

        '''
        print('Closing Application, and saving current settings to file.')
        self.settingsSave()