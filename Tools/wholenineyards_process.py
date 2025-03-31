# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

import os
import csv
import numpy as np
import cv2
import scipy
import glob
import math

class WorkerThread(QThread):
    
    image_count = pyqtSignal(int)
    message = pyqtSignal(str)
    
    def __init__(self, inputDir, calib_file, calib_folder, colormaps, raw_tif_files, despeckle, flipHorizontal, invertImage, autoscale, autofil, rawCopy, nucCopy, badpixelCopy, invertedCopy, despeckleCopy, pixelMaskFilePath):
        super().__init__()
        self.inputDir = inputDir
        self.calib_file = calib_file
        self.calib_folder = calib_folder
        self.colormaps = colormaps
        self.raw_tif_files = raw_tif_files
        
        # not used, as they are essential
        self.despeckle = despeckle
        self.flipHorizontal = flipHorizontal
        self.invertImage = invertImage
        self.autoscale = autoscale
        self.autofil = autofil
        
        # used to dedfine what to save to disk
        self.rawCopy = rawCopy
        self.nucCopy = nucCopy
        self.badpixelCopy = badpixelCopy
        self.invertedCopy = invertedCopy
        self.despeckleCopy = despeckleCopy

        self.pixelMaskFilePath = pixelMaskFilePath

        self.completed_images = []        
        
        self.ancillary_data = []
        self.bad_pixels = []
        with open(self.pixelMaskFilePath, 'r', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                self.bad_pixels.append([int(row[1])-1,int(row[0])-1])
            np.save(os.path.join(os.path.dirname(self.inputDir), 'bad_pixels.npy'), self.bad_pixels)
        

    # def progressImagesfunction(self, progress):
    #     self.completed_images.append(progress)
    #     self.image_count.emit(len(self.completed_images))
    
    def run(self):
        
        self.image_count.emit(0)
        self.message.emit('Reading Ancillary Data...')
        
        # read the first image and check how many extra columns we have
        first_raw_tif = cv2.imread(self.raw_tif_files[0], cv2.IMREAD_UNCHANGED)
        height, width = first_raw_tif.shape[:2]
        
        # extract ancillary data 
        image_counter = 0
        for raw_tif_file in self.raw_tif_files:
            raw_tif = cv2.imread(raw_tif_file, cv2.IMREAD_UNCHANGED)
            self.ancillary_data.append(raw_tif[0:height, 1280:width])
            image_counter += 1
            self.image_count.emit(image_counter)
        
        if self.rawCopy:
            self.image_count.emit(0)
            self.message.emit('Making copies of all Raw Images...') 
            
            # create copy of raw images without ancillary data
            foldername_01 = '01_raw_wo_ancillary_data'
            output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_01)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            image_counter = 0
            for image in os.listdir(self.inputDir):
                if os.path.isfile(os.path.join(self.inputDir, image)) and image.endswith('.tif'):
                    ImageMat = cv2.imread(os.path.join(self.inputDir, image), cv2.IMREAD_UNCHANGED)[0:1024, 0:1280]
                    cv2.imwrite(os.path.join(output_folder, image), ImageMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
                    image_counter += 1
                    self.image_count.emit(image_counter)
        
        self.image_count.emit(0)
        self.message.emit('Performing NUC on all images...')
        
        # prepare for calibration
        foldername_02 = '02_nuc_wo_ancillary'
        
        #
        input_folder = self.inputDir
        #
        
        output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_02)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # perform nuc
        os.chdir(self.inputDir)

        input_location = r'{}'.format(self.inputDir)
        output_loc = r'{}'.format(output_folder)
        if not os.path.exists(output_loc):
            os.makedirs(output_loc)
        os.chdir(input_location)
        
        images = glob.glob("*tif")
        os.chdir(r'{}'.format(self.calib_folder))
        file = open("images_to_process.txt", "w")
        file.writelines("# SVuNtcApplySettings \n")
        file.writelines("version=1 \n")
        file.writelines("# The calibration to be applied to images.\n")
        file.writelines("""calibration = "{}"\n""".format(self.calib_file))
        file.writelines("# Folder containing the input images.\n")
        file.writelines("""image_folder="{}"\n""".format(input_location))
        file.writelines("# Folder where the corrected images will be stored.\n")
        file.writelines("""output_folder="{}"\n""".format(output_loc))
        
        for image in images:
            file.writelines("image={}\n".format(image))
        file.close()
        
        import subprocess
        os.chdir(self.calib_folder)
        subprocess.run(["SvuNtcApply.exe", "images_to_process.txt"])
        
        self.image_count.emit(0)
        self.message.emit('Processing all images...')
        
        if self.nucCopy:
            foldername_03 = '03_nuc_w_ancillary'
            output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_03)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder) 
        
        if self.badpixelCopy:
            foldername_04 = '04_nuc_w_ancillary_bad_pixels_corrected'
            output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_04)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
        
        if self.invertedCopy:
            foldername_05 = "05_nuc_w_ancillary_inverted"
            output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_05)        
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
        
        if self.despeckleCopy:
            foldername_06 = "06_nuc_w_ancillary_despeckled"
            output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_06)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
        
        foldername_07 = "07_nuc_w_ancillary_scaled"
        output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_07) 
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        foldername_08 = "08_prettify"
        output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_08)      
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)  
            
            
        foldername_09 = "09_videos"
        output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_09)     
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        np.save(os.path.join(os.path.dirname(self.inputDir), 'ancillary_data.npy'), self.ancillary_data)
             
        input_folder = os.path.join(os.path.dirname(self.inputDir), foldername_02)
        image_counter = 0
        for image in os.listdir(input_folder):
            if os.path.isfile(os.path.join(input_folder, image)) and image.endswith('.tif'):
                # read in image
                ImageMat = cv2.imread(os.path.join(input_folder, image), cv2.IMREAD_UNCHANGED)
        
                # Write NUC image with ancillary Data
                if self.nucCopy:
                    foldername_03 = '03_nuc_w_ancillary'
                    output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_03)
                    ImageWithAncilMat = cv2.hconcat([ImageMat, self.ancillary_data[image_counter]])
                    cv2.imwrite(os.path.join(output_folder, image), ImageWithAncilMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
        
                # Perform Bad Pixel Correction using bad-pixel map
                # THIS IS THE THING WHICH MAKES THE PROCESS TAKE A WHILE 
                for i in range(8):
                    for bad_pixel in self.bad_pixels:
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
                
                # write bad pixel corrected image
                if self.badpixelCopy:
                    foldername_04 = '04_nuc_w_ancillary_bad_pixels_corrected'
                    output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_04)         
                    ImageWithAncilMat = cv2.hconcat([ImageMat, self.ancillary_data[image_counter]])
                    cv2.imwrite(os.path.join(output_folder, image), ImageWithAncilMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
                
                # Invert image 
                ImageMat = np.invert(ImageMat)
                
                # write inverted image
                if self.invertedCopy:
                    foldername_05 = "05_nuc_w_ancillary_inverted"
                    output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_05)   
                    ImageWithAncilMat = cv2.hconcat([ImageMat, self.ancillary_data[image_counter]])
                    cv2.imwrite(os.path.join(output_folder, image), ImageWithAncilMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
                
                # De-speckle Image
                ImageMat = scipy.signal.medfilt2d(ImageMat)
                ImageMat[0, 0] = np.median([ImageMat[0, 1], ImageMat[1, 0], ImageMat[1, 1]])
                ImageMat[1023, 0] = np.median([ImageMat[1022, 0], ImageMat[1022, 1], ImageMat[1023, 1]])
                ImageMat[0, 1279] = np.median([ImageMat[0, 1278], ImageMat[1, 1278], ImageMat[1, 1279]])
                ImageMat[1023, 1279] = np.median([ImageMat[1022, 1279], ImageMat[1022, 1278], ImageMat[1023, 1278]])      
                
                # write despeckled image
                if self.despeckleCopy:
                    foldername_06 = "06_nuc_w_ancillary_despeckled"
                    output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_06)
                    ImageWithAncilMat = cv2.hconcat([ImageMat, self.ancillary_data[image_counter]])
                    cv2.imwrite(os.path.join(output_folder, image), ImageWithAncilMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
                
                # Scale Images
                foldername_07 = "07_nuc_w_ancillary_scaled"
                output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_07) 
                percent_high = np.percentile(ImageMat, 99.97)
                percent_low = np.percentile(ImageMat, 0.07)
                ImageMat = np.clip(((ImageMat - percent_low) * ((math.pow(2, 16) - 1) / (percent_high - percent_low))), 0.0, math.pow(2, 16) - 1).astype('uint16')
                ImageWithAncilMat = cv2.hconcat([ImageMat, self.ancillary_data[image_counter]])
                cv2.imwrite(os.path.join(output_folder, image), ImageWithAncilMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))    
                    
                # prettify
                foldername_08 = "08_prettify"
                output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_08)      
                for colormap in self.colormaps:
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
                        
                    colormapFolderName = os.path.join(output_folder, colormapName)
                    if not os.path.exists(colormapFolderName):
                        os.makedirs(colormapFolderName)   
                    colorImageMat = cv2.applyColorMap((ImageMat/256).astype('uint8'), colormap)
                    if self.flipHorizontal:
                        cv2.imwrite(os.path.join(colormapFolderName, image), cv2.flip(colorImageMat, 1), params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
                    else:
                        cv2.imwrite(os.path.join(colormapFolderName, image), colorImageMat, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
                
                image_counter += 1
                self.image_count.emit(image_counter)
        
        
        self.image_count.emit(0)
        self.message.emit('Generating Videos...')
        
        foldername_09 = "09_videos"
        output_folder = os.path.join(os.path.dirname(self.inputDir), foldername_09)     
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        input_folder = os.path.join(os.path.dirname(self.inputDir), foldername_08)
        
        for colorfolder in os.listdir(input_folder):
            if os.path.isdir(os.path.join(input_folder, colorfolder)):
                self.image_count.emit(0)
                self.message.emit('Generating ' + os.path.basename(colorfolder) + ' Video')
                colorinput_folder = os.path.join(input_folder, colorfolder)
                
                # get all tif files in the input folder
                tif_files = glob.glob(colorinput_folder + '/*.tif')
                
                # read the first image to get dimensions and initialize video writer
                first_tif = cv2.imread(tif_files[0], cv2.IMREAD_UNCHANGED)
                
                height, width = first_tif.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'H264') # change codec as needed
                
                video_writer = cv2.VideoWriter(os.path.join(output_folder, os.path.basename(colorfolder) + '.mpeg') , fourcc, 25.0, (width, height), True)
                
                image_counter = 0
                for tif_file in tif_files:
                    tif_image = cv2.imread(tif_file, cv2.IMREAD_UNCHANGED)
                    video_writer.write(tif_image)
                    image_counter += 1
                    self.image_count.emit(image_counter)
                video_writer.release()

def updateProgressDialogProgress(self, progress):
    self.progressDialog.setValue(progress)
    self.progressDialog.show()
    
def updateProgressDialogText(self, text):
    self.progressDialog.setLabelText(text)
    self.progressDialog.show()

def WholeNineYards(ui):    

    ui.colormaps = []
    
    if ui.checkBoxColormapJet_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_JET)
    if ui.checkBoxInferno_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_INFERNO)
    if ui.checkBoxRainbow_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_RAINBOW)
    if ui.checkBoxHot_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_HOT)
    if ui.checkBoxHSV_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_HSV)
    if ui.checkBoxViridis_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_VIRIDIS)
    if ui.checkBoxOcean_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_OCEAN)
    if ui.checkBoxTwilightShifted_2.isChecked():
        ui.colormaps.append(cv2.COLORMAP_TWILIGHT_SHIFTED)

    inputDir = ui.WNYInputDirPath.text()
    calib_file = ui.NUCFilePath.text()
    calib_folder = os.path.dirname(calib_file)
    colormaps = ui.colormaps

    despeckle = ui.checkBoxDespeckle_2.isChecked()
    flipHorizontal = ui.checkBoxFlipHorizontal_2.isChecked()
    invertImage = ui.checkBoxInvertImageData_2.isChecked()
    autoscale = ui.checkBoxAutoscaleDynamicRange_2.isChecked()
    autofil = ui.checkBoxAutofillBadPixels_2.isChecked()
    rawCopy = ui.checkBoxRawWithoutAncil.isChecked()
    nucCopy = ui.checkBoxNUCWithAncil.isChecked()
    badpixelCopy = ui.checkBoxSaveBadPixel.isChecked()
    invertedCopy = ui.checkBoxSaveInverted.isChecked()
    despeckleCopy = ui.checkBoxSaveDespeckled.isChecked()
    
    raw_tif_files = glob.glob(inputDir + '/*.tif')

    number_of_images = len(raw_tif_files)
    
    ui.progressDialog = QProgressDialog("Processing all images...", None, 0, number_of_images, ui)
    ui.progressDialog.setWindowTitle("Please wait...")
    ui.progressDialog.setWindowModality(Qt.ApplicationModal)
    
    worker = WorkerThread(inputDir, calib_file, calib_folder, colormaps, raw_tif_files, despeckle, flipHorizontal, invertImage, autoscale, autofil, rawCopy, nucCopy, badpixelCopy, invertedCopy, despeckleCopy, ui.pixelMaskFilePath.text())
    
    worker.image_count.connect(updateProgressDialogProgress)
    worker.message.connect(updateProgressDialogText)
    worker.started.connect(ui.progressDialog.show)
    worker.finished.connect(ui.progressDialog.close)
    worker.start()