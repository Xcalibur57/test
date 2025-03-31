# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import os


def generateReport(ui, folderName, aoiPoint):
    '''
    Function which generates a single page report (as a .png file) for a single field position's MTF stacked analysis

    Parameters
    ----------
    folderName: String
        String variable which is used to describe the specific MTF dataset that was used to generate the report.
    aoiPoint: QPoint
        QPoint object, current unused.
    '''
    
    fig = plt.figure(figsize = (11, 15.5), dpi = 200)
    gs = gridspec.GridSpec(nrows = 3, ncols = 2, height_ratios = [0.6, 1, 1.4])
    
    flipped = 1
    
    if ui.EsfPosition[0] > ui.EsfPosition[-1]: # backwards
        if ui.EsfData[0] < ui.EsfData[-1]:
            flipped = -1
    else:   #forwards
        if ui.EsfData[0] > ui.EsfData[-1]:
            flipped = -1
            
    esf_min = np.min(ui.EsfData) - 0.05 * (np.max(ui.EsfData) - np.min(ui.EsfData))
    esf_max = np.max(ui.EsfData) + 0.05 * (np.max(ui.EsfData) - np.min(ui.EsfData))
    
    displayMat = ui.aoiImageMat.copy()
    for y in range(displayMat.shape[0]):
        for x in range(displayMat.shape[1]):
            if displayMat[y, x] > esf_max:
                displayMat[y, x] = esf_max
            if displayMat[y, x] < esf_min:
                displayMat[y, x] = esf_min
    
    ax0 = fig.add_subplot(gs[0,1])
    ax0.imshow(displayMat)
    
    ax1 = fig.add_subplot(gs[1,0])
    ax1.plot(ui.EsfRawPosition_new * flipped, ui.EsfRawData_new, 'b.', label = 'Raw Data')
    ax1.plot(ui.EsfRawPosition_removed * flipped, ui.EsfRawData_removed, 'r.', label = 'Removed Noise')
    ax1.plot(ui.EsfPosition * flipped, ui.EsfData, 'r-', label = 'Best Fit')
    ax1.set_ylim(esf_min, esf_max)
    ax1.grid()
    ax1.set_xlabel('Distance fom Edge [px]')
    ax1.set_ylabel('Pixel Value [ADU]')
    ax1.set_title('ESF')
    ax1.legend()
    
    ax2 = fig.add_subplot(gs[1,1])
    ax2.plot(ui.EsfPosition * flipped, ui.LSF * flipped, 'b-')
    ax2.grid()
    ax2.set_xlabel('Distance from Edge [px]')
    ax2.set_ylabel('Gradient of ESF [ADU/px]')
    ax2.set_title('LSF')
    
    ax3 = fig.add_subplot(gs[2:, :])
    half_nyquist = np.interp(32.5, ui.frequency, ui.FFT)
    ax3.plot(ui.frequency, ui.FFT, '-r', label = 'System Stacked MTF')
    ax3.plot(32.5, half_nyquist, 'ob', label = 'Stacked Half-Nyquist = {:.3f}'.format(half_nyquist))
    ax3.set_xlabel('Spatial Frequency [lp/mm]')
    ax3.set_ylabel('Modulus of the OTF')
    ax3.set_ylim(0, 1.05)
    ax3.set_xlim(0, 65)
    ax3.set_title('MTF')
    ax3.grid()
    ax3.legend()

    plt.text(-0.075, 1.7, 'Stacked MTF:  ' + folderName,
                fontsize = 'x-large', fontweight = 'bold',
                horizontalalignment = 'left',
                verticalalignment = 'bottom',
                transform = ax1.transAxes)
    
    plt.text(-0.075, 1.68, os.path.dirname(ui.bulk_dir_name) + '\n\n'
                '10% - 90% Edge Width:  ' + str(ui.width10_90) + '\n'
                '20% - 80% Edge Width:  ' + str(ui.width20_80) + '\n\n'
                'Length of Edge:  ' + str(ui.lengthOfEdgeLine.value()) + '\n'
                'Normal Distance to Edge:  ' + str(ui.normalDistanceFromEdge.value()) + '\n'
                'Oversampling Per Pixel:  ' + str(ui.oversamplingMultiplier.value()) + '\n\n'
                'MTF @ 0.25x Nyquist:  {:.1f}%'.format(100 * np.interp(16.25, ui.frequency, ui.FFT)) + '\n'
                'MTF @ 0.50x Nyquist:  {:.1f}%'.format(100 * np.interp(32.50, ui.frequency, ui.FFT)) + '\n'
                'MTF @ 0.75x Nyquist:  {:.1f}%'.format(100 * np.interp(48.75, ui.frequency, ui.FFT)) + '\n'
                'MTF @ 1.00x Nyquist:  {:.1f}%'.format(100 * np.interp(65.00, ui.frequency, ui.FFT)) + '\n\n'
                'Number of Stacked Images:  ' + str(ui.number_of_images_processed) + '\n',
                horizontalalignment = 'left',
                verticalalignment = 'top', 
                transform = ax1.transAxes)
            
    plt.subplots_adjust(bottom = 0.05, left = 0.1, right = 0.95, top = 0.95, wspace = 0.24, hspace = 0.24)
    plt.savefig(ui.bulk_dir_name + "/stacked_datasheet" + folderName + ".png")